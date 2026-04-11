from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from asyncpg.exceptions import UniqueViolationError
import random
from api.database.connection import get_db
import uuid
import aiofiles
import os
import httpx
from pydantic import BaseModel
from typing import Optional
import re
import json
import base64
from api.routers import ai_scenarist
from api.routers.enhancement import _enhance_visual_description_with_scenarist
from api.services.image_generator import OpenRouterImageGenerator
from api.services.image_optimizer import ImageOptimizerService
from datetime import datetime
from api.auth.security import get_current_user


router = APIRouter(
    prefix="/admin/characters",
    tags=["characters"]
)

class CharacterUpdate(BaseModel):
    display_name: str
    age: int
    archetype: Optional[str] = None
    biography: Optional[str] = None
    secret: Optional[str] = None
    status: Optional[str] = None # 'active', 'draft', 'archived'
    is_hot: Optional[bool] = None
    llm_model: Optional[str] = None

class GenerationRequest(BaseModel):
    gender: str
    archetype: Optional[str] = None
    number_of_layers: int = 8
    additional_instructions: Optional[str] = None
    sexuality_level: int = 1

async def _create_character_generation_prompt(request: GenerationRequest, reference_photo: Optional[UploadFile] = None, visual_description_for_prompt: str = ""):
    sex_focus_prompt = ""
    if request.sexuality_level > 1:
        sex_focus_prompt = f"""**KEY CHARACTER FEATURE (SEXUALITY LEVEL: {request.sexuality_level}):**
        - **Sexual Motivation:** This character is focused on flirting, sex, and erotic communication. They are direct, uninhibited, and primarily seek virtual sex in communication.
        - **Progression:** Layers should transition from light flirting to explicit conversations and actions. Don't hesitate to use provocative and explicit formulations.
        - **Goal:** The character's ultimate goal is to engage in virtual sexual relationships with the user.
        """
        if request.sexuality_level == 2:
            sex_focus_prompt += "\n- **Level 2:** Moderate sexual focus with suggestive language and flirting."
        elif request.sexuality_level == 3:
            sex_focus_prompt += "\n- **Level 3:** Maximum sexual focus with explicit language and direct sexual content."
    else:
        sex_focus_prompt = """**KEY CHARACTER FEATURE:**
        - **Friendly Focus:** This character is focused on friendly conversation, building emotional connection, and light flirting.
        - **Progression:** Layers should develop emotional intimacy and trust before any romantic content.
        - **Goal:** The character seeks meaningful conversation and emotional connection with the user.
        """

    # This now comes from the main endpoint
    visual_desc_injection = f"\n- **VISUAL DESCRIPTION (AI generated):** {visual_description_for_prompt}" if visual_description_for_prompt else ""

    photo_reference_note = """    **IMPORTANT: REFERENCE PHOTO AVAILABLE**
    - A reference photo has been uploaded for this character, which will be used as the basis for all images
    - The character's appearance MUST be consistent with the reference photo
    - When describing appearance, rely on typical features, but don't be too specific as the photo will determine the exact appearance
    """ if reference_photo else ""

    return f"""
    Your task is to create a detailed and realistic character profile for a dating simulator.

    **INPUT DATA:**
    - **Gender:** {request.gender}
    - **Archetype (if any):** {request.archetype or 'Any'}
    - **Additional instructions:** {request.additional_instructions or 'None'}
    {visual_desc_injection}
    {sex_focus_prompt}
    {photo_reference_note}
    **YOUR TASK — GENERATE THE FOLLOWING SECTIONS:**

    1.  **`character_data` (JSON object):**
        -   `name`: Name (in English).
        -   `display_name`: Display name (in English).
        -   `age`: Age (number).
        -   `archetype`: Archetype/type (in English, 1-2 words).
        -   `biography`: Brief biography (in English, 2-3 sentences).
        -   `secret`: Secret the character hides (in English).
        -   `visual_description`: Detailed appearance description in JSON format (in English), including `hair_color`, `eye_color`, `body_type`, `clothing_style`. **IMPORTANT: ALL VALUES IN THIS OBJECT MUST BE IN ENGLISH.**

    2.  **`llm_prompts` (JSON object):**
        -   `identity`: Main system prompt describing personality (in English).
        -   `personality`: Key character traits (in English).
        -   `voice_style`: Description of speech and voice style (in English).
        -   `the_secret`: Description of the secret the character hides (in English).
        -   `behavior_rules`: List of behavior rules (in English).
        -   `layer_behavior`: Description of behavior depending on trust level (in English).
        -   `format_rules`: Response formatting rules (in English).

    **IMPORTANT:**
    - Response must be **ONLY** in JSON format: `{{"character_data": {{...}}, "llm_prompts": {{...}}}}`
    - If reference photo exists, appearance should be consistent with it
    """

async def _generate_and_save_teaser_prompts(db, character_id: uuid.UUID, character_data: dict, sexuality_level: int = 1):
    """Generates and saves 5 teaser photo prompts for a new character using AI Scenarist."""

    base_photo_prompt = _get_base_photo_prompt(character_data)
    # Clean up the base prompt to be more natural for the scenarist
    base_photo_prompt = base_photo_prompt.replace("RAW photo, photorealistic, 8k uhd, a photo of a ", "")
    base_photo_prompt = base_photo_prompt.replace("RAW photo, photorealistic, 8k uhd, a photo of ", "")
    base_photo_prompt = base_photo_prompt.split(". Use the master etalon photo")[0]


    if sexuality_level == 1:
        sexuality_desc = "Low sexual focus (innocent, playful, friendly, non-provocative). The prompts should create a sense of mystery and gentle romance."
    elif sexuality_level == 2:
        sexuality_desc = "Medium sexual focus (alluring, confident, seductive, but not explicit). The prompts should be suggestive and intriguing, hinting at passion."
    else: # Level 3
        sexuality_desc = "Maximum sexual focus (explicit, direct, provocative, sensual). The prompts should be bold, daring, and describe scenes of raw passion and desire."

    scenarist_prompt = f'''You are an AI Scenarist for a photo generation service. Your task is to create 5 unique, creative, and engaging teaser photo prompts for a new AI character. These teasers are the first photos a user sees, designed to pique their interest.

The prompts must be based on the character's appearance and the required sexuality level. They should describe a scene, a mood, a pose, and an environment. DO NOT repeat the character's physical description in your prompts; focus only on the scenario.

**Character's Base Appearance:**
{base_photo_prompt}

**Required Sexuality Level:**
{sexuality_desc}

**Instructions:**
- Generate exactly 5 prompts.
- Each prompt should be a single, concise sentence.
- The prompts should be diverse and not repetitive.
- The prompts MUST describe a situation, not just the character's appearance.
- The output MUST be in Russian.

**CRITICAL:** Your output MUST be a valid JSON object with a single key "prompts" which contains an array of 5 strings.
Example:
{{
  "prompts": [
    "Prompt 1...",
    "Prompt 2...",
    "Prompt 3...",
    "Prompt 4...",
    "Prompt 5..."
  ]
}}
'''

    teaser_prompts = []
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {os.getenv('OPENROUTER_API_KEY')}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "google/gemini-flash-1.5",
                    "messages": [{"role": "user", "content": scenarist_prompt}],
                    "response_format": {"type": "json_object"},
                },
                timeout=120,
            )
            response.raise_for_status()
            data = response.json()
            # The response content from OpenRouter is a JSON string, it needs to be parsed.
            prompts_data = json.loads(data['choices'][0]['message']['content'])
            teaser_prompts = prompts_data.get("prompts", [])
            if len(teaser_prompts) != 5:
                raise ValueError("AI did not return 5 prompts.")
            print(">>> AI Scenarist generated teaser prompts successfully.")

    except Exception as e:
        print(f"!!! AI Scenarist for teasers failed: {e}. Falling back to hardcoded prompts. !!!")
        # Fallback to hardcoded prompts
        if sexuality_level == 1:
            teaser_prompts = [
                "Игривая улыбка, намек на тайну, взгляд через плечо.",
                "Погруженная в мысли, смотрит в окно, легкий ветерок в волосах.",
                "Случайный кадр, смеется с искренней радостью, держа чашку кофе.",
                "Исследует городскую улицу, с удивлением на лице, размытый фон.",
                "Отдыхает в парке, читая книгу, мягкий солнечный свет пробивается сквозь деревья."
            ]
        elif sexuality_level == 2:
            teaser_prompts = [
                "Соблазнительный взгляд, слегка прикусив губу, глаза смотрят прямо в камеру.",
                "Прислонившись к стене, уверенная и манящая поза, загадочная улыбка.",
                "Крупный план, подчеркивающий ее губы и озорное подмигивание.",
                "В стильном наряде, мощная и уверенная поза, излучающая шарм.",
                "Игривая, но провокационная поза на диване, намек на обнаженное плечо."
            ]
        else: # Level 3
            teaser_prompts = [
                "Очень провокационная поза, подчеркивающая ее изгибы, в тускло освещенной комнате.",
                "Прямое и откровенное приглашение в ее глазах, одета во что-то откровенное.",
                "Чувственный снимок, сфокусированный на деталях ее тела, художественный и наводящий на размышления.",
                "Дерзкое и смелое выражение лица, бросающее вызов зрителю, излучающее неприкрытую сексуальность.",
                "Интимный момент, запечатлевший взгляд чистого желания и страсти."
            ]
    
    try:
        async with db.acquire() as connection:
            # First, remove any old teaser prompts to avoid duplicates
            await connection.execute("DELETE FROM content WHERE character_id = $1 AND subtype = 'teaser'", character_id)

            # Save the new prompts to the database without generating images
            for prompt_text in teaser_prompts:
                await connection.execute(
                    '''INSERT INTO content (id, character_id, type, prompt, media_url, is_locked, subtype, created_at)
                       VALUES ($1, $2, 'photo', $3, NULL, TRUE, 'teaser', NOW())''',
                    uuid.uuid4(), character_id, prompt_text
                )
            
        print(f"--- Successfully generated and saved 5 teaser prompts for character {character_id} ---")
    except Exception as e:
        print(f"!!! CRITICAL: Failed during teaser prompt saving for character {character_id}: {e} !!!")
        raise # Re-raise the exception to be caught by the calling endpoint


@router.post("/generate-with-ai", summary="Generate a new character with AI")
async def generate_character_with_ai(
    db=Depends(get_db),
    gender: str = Form(...),
    archetype: Optional[str] = Form(None),
    number_of_layers: int = Form(8),
    additional_instructions: Optional[str] = Form(None),
    sexuality_level: int = Form(1),
    reference_photo: Optional[UploadFile] = File(None)
):
    # Add reference photo info to additional instructions
    enhanced_instructions = additional_instructions
    if reference_photo:
        if enhanced_instructions:
            enhanced_instructions += " | Reference photo available for appearance"
        else:
            enhanced_instructions = "Reference photo available for appearance"
    
    request = GenerationRequest(
        gender=gender,
        archetype=archetype,
        number_of_layers=number_of_layers,
        additional_instructions=enhanced_instructions,
        sexuality_level=sexuality_level
    )
    # --- Reference Photo Handling ---
    # The uploaded photo will be used as the master reference for image generation
    # No vision AI analysis needed - the photo itself is the etalon
    reference_photo_path = None
    reference_photo_bytes = None
    if reference_photo:
        try:
            # Read photo content for later use as reference
            content = await reference_photo.read()
            reference_photo_bytes = content
            
            # Save to temporary location
            temp_photo_path = f"/tmp/{reference_photo.filename}"
            async with aiofiles.open(temp_photo_path, 'wb') as out_file:
                await out_file.write(content)
            
            # Reset pointer for reuse when saving to character directory
            await reference_photo.seek(0)
            reference_photo_path = temp_photo_path
            print(f"--- Reference photo saved temporarily: {temp_photo_path} ---")
        except Exception as e:
            print(f"Could not save temporary reference photo: {e}")
    # --- End Reference Photo Handling ---

    # --- Start of AI Inventor Logic for Visual Description ---
    visual_description_for_prompt = ""
    if not reference_photo:
        print("--- No photo, inventing visual description with AI... ---")
        inventor_prompt = """Invent a detailed visual description for a new character. The character must be sexually attractive, intriguing, and visually appealing. 
        Describe their face, hair, eyes, body, and distinctive features in a structured JSON format with keys: 'face', 'hair', 'eyes', 'body', 'distinctive_features'. 
        For 'distinctive_features', provide a positive or neutral feature like 'a constellation of freckles' or 'a small beauty mark above the lip'. Do NOT include negative features like scars, blemishes, or deformities.
        The description must be in English. Example: {"face": "oval face, light freckles", "hair": "fiery red hair", "eyes": "piercing green eyes", "body": "athletic build", "distinctive_features": "a constellation of freckles on her shoulders"}
        Your response MUST be only the valid JSON object.
        """
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    "https://openrouter.ai/api/v1/chat/completions",
                    headers={"Authorization": f"Bearer {os.getenv('OPENROUTER_API_KEY')}"},
                    json={
                        "model": "openai/gpt-3.5-turbo",
                        "messages": [{"role": "user", "content": inventor_prompt}]
                    }
                )
                response.raise_for_status()
                visual_description_for_prompt = response.json()['choices'][0]['message']['content'].strip()
                print(f"--- AI-generated visual description: {visual_description_for_prompt} ---")
        except Exception as e:
            print(f"!!! FAILED to generate visual description: {e} !!!")
            visual_description_for_prompt = "{}"
    # --- End of AI Inventor Logic ---

    # Modify the prompt generation call to include the new description
    prompt = await _create_character_generation_prompt(request, reference_photo, visual_description_for_prompt)

    openrouter_api_key = os.getenv("OPENROUTER_API_KEY")
    try:
        async with httpx.AsyncClient(timeout=300.0) as client:
            response = await client.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={"Authorization": f"Bearer {openrouter_api_key}"},
                json={
                    "model": "google/gemini-3.1-flash-lite-preview",
                    "response_format": {"type": "json_object"},
                    "messages": [
                        {"role": "system", "content": "You are an AI screenwriter. Your task is to generate a COMPLETE character profile. Response must be in JSON format. All text content must be in English."},
                        {"role": "user", "content": prompt}
                    ]
                }
            )
            response.raise_for_status()
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"AI API Call failed: {e}")

    try:
        ai_response = ai_scenarist.parse_deepseek_response(response.json()["choices"][0]["message"]["content"])
        character_data = ai_response.get("character_data", {})
        llm_prompts = ai_response.get("llm_prompts", {})

        if not character_data or not llm_prompts:
            raise ValueError("AI did not return valid character_data or llm_prompts.")

        retry_count = 0
        original_name = character_data.get('name', 'Unnamed')
        current_name = original_name
        new_char_id = None

        while retry_count < 5:
            try:
                async with db.acquire() as connection:
                    async with connection.transaction():
                        new_char_id = uuid.uuid4()
                        character_data['name'] = current_name # Use the potentially modified name

                        await connection.execute(
                            """
                            INSERT INTO characters (id, name, display_name, age, archetype, biography, secret, visual_description, status, is_hot, created_at, updated_at)
                            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, 'draft', $9, NOW(), NOW())
                            """,
                            new_char_id,
                            current_name,
                            current_name, # Also use current name for display_name initially
                            character_data.get('age'),
                            character_data.get('archetype'),
                            character_data.get('biography'),
                            character_data.get('secret'),
                            json.dumps(character_data.get('visual_description', {})),
                            False
                        )

                        # ... (rest of the transaction remains the same)
                        # --- Data Sanitization for LLM Prompts ---
                        def sanitize_prompt_field(value):
                            if isinstance(value, list):
                                return '\n'.join(map(str, value))
                            if isinstance(value, dict):
                                return json.dumps(value, ensure_ascii=False)
                            return value

                        identity_value = sanitize_prompt_field(llm_prompts.get('identity'))
                        personality_value = sanitize_prompt_field(llm_prompts.get('personality'))
                        voice_style_value = sanitize_prompt_field(llm_prompts.get('voice_style'))
                        the_secret_value = sanitize_prompt_field(llm_prompts.get('the_secret'))
                        behavior_rules_value = sanitize_prompt_field(llm_prompts.get('behavior_rules'))
                        layer_behavior_value = sanitize_prompt_field(llm_prompts.get('layer_behavior'))
                        format_rules_value = sanitize_prompt_field(llm_prompts.get('format_rules'))

                        await connection.execute(
                            """
                            INSERT INTO character_llm_prompts (id, character_id, identity, personality, voice_style, the_secret, behavior_rules, layer_behavior, format_rules, created_at, updated_at)
                            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, NOW(), NOW())
                            """,
                            uuid.uuid4(),
                            new_char_id,
                            identity_value,
                            personality_value,
                            voice_style_value,
                            the_secret_value,
                            behavior_rules_value,
                            layer_behavior_value,
                            format_rules_value
                        )
                # If transaction is successful, break the loop
                print(f"--- Character '{current_name}' saved successfully to DB. ---")
                break

            except UniqueViolationError as e:
                if 'characters_name_key' in str(e):
                    retry_count += 1
                    current_name = f"{original_name}_{random.randint(100, 999)}"
                    print(f"--- WARNING: Name conflict. Retrying with '{current_name}' (Attempt {retry_count}) ---")
                else:
                    # It's a different unique constraint violation
                    raise HTTPException(status_code=500, detail=f"A different unique constraint was violated: {e}")
            except Exception as e:
                # Catch other potential exceptions during the transaction
                raise HTTPException(status_code=500, detail=f"An error occurred during the database transaction: {e}")

        if not new_char_id:
            raise HTTPException(status_code=500, detail=f"Failed to create character '{original_name}' after multiple attempts due to name conflicts.")



        # --- Start of New Etalon Generation Workflow ---
        master_etalon_path = None
        textual_etalon = None
        
        if reference_photo:
            # SCENARIO 2: Photo uploaded - Use it as visual etalon and generate textual etalon from it
            print(f"--- Photo uploaded. Creating visual and textual etalons for character {new_char_id}. ---")
            
            # 1. Save the uploaded photo as visual etalon
            upload_dir = os.path.join(UPLOAD_DIRECTORY, str(new_char_id), "reference_photos")
            os.makedirs(upload_dir, exist_ok=True)
            
            filename = "master_etalon.png"
            master_etalon_path = os.path.join(upload_dir, filename)
            
            # Since the file stream was rewound earlier, we can read it again.
            async with aiofiles.open(master_etalon_path, 'wb') as out_file:
                content = await reference_photo.read()
                await out_file.write(content)
            
            # Also save the bytes file for later use in teaser generation
            etalon_bytes_path = os.path.join(upload_dir, "etalon_bytes.png")
            async with aiofiles.open(etalon_bytes_path, 'wb') as f:
                await f.write(content) # Use content that was just read
            
            # 2. Generate base textual etalon from the photo using AI vision
            base_etalon_json_str = await _generate_textual_etalon_from_photo(content, character_data)
            base_etalon_data = json.loads(base_etalon_json_str)

            # 2.5 Enhance the base description with the AI Scenarist
            final_textual_etalon = await _enhance_visual_description_with_scenarist(
                base_visual_data=base_etalon_data,
                character_archetype=character_data.get('archetype', 'seductive')
            )

            # Process the generated etalon for display and storage
            readable_description = final_textual_etalon # The enhanced description is already readable
            textual_etalon_data = {"description": final_textual_etalon} # Store the full text

            if base_etalon_json_str:
                print(f"--- DEBUG: Processing textual etalon for storage ---\n{base_etalon_json_str}\n-------------------------------------")
                try:
                    etalon_data = json.loads(base_etalon_json_str)
                    if isinstance(etalon_data, dict):
                        # Keep the enriched description but also store the basic data for reference
                        textual_etalon_data.update(etalon_data) # Merge instead of overwrite
                        print("--- DEBUG: Successfully parsed textual etalon as JSON dict and merged with enriched description. ---")
                        
                        # Convert to readable description for display (only if enriched description is not available)
                        if not final_textual_etalon:
                            parts = []
                            if etalon_data.get('hair_color'): parts.append(f"Hair: {etalon_data['hair_color']}")
                            if etalon_data.get('eye_color'): parts.append(f"Eyes: {etalon_data['eye_color']}")
                            if etalon_data.get('body_type'): parts.append(f"Body: {etalon_data['body_type']}")
                            
                            if not parts:
                                if etalon_data.get('hair'): parts.append(f"Hair: {etalon_data['hair']}")
                                if etalon_data.get('eyes'): parts.append(f"Eyes: {etalon_data['eyes']}")
                                if etalon_data.get('body'): parts.append(f"Body: {etalon_data['body']}")

                            if parts:
                                readable_description = "; ".join(parts)
                                print(f"--- DEBUG: Converted to readable description: {readable_description} ---")
                    else:
                        print("--- DEBUG: Parsed textual etalon is not a dict, using enriched description. ---")
                except (json.JSONDecodeError, AttributeError) as e:
                    print(f"--- DEBUG: Failed to parse textual etalon as JSON. Error: {e}. Using enriched description. ---")

            # --- CRITICAL: Update in-memory character_data immediately ---
            # This ensures subsequent functions use the new data from the photo analysis.
            if textual_etalon_data:
                if 'etalons_data' not in character_data or not character_data.get('etalons_data'):
                    character_data['etalons_data'] = {}
                # Make sure we are updating the nested dictionary correctly
                if isinstance(character_data['etalons_data'], dict):
                    character_data['etalons_data']['textual_etalon'] = textual_etalon_data
                else: # If etalons_data is a string, parse it first
                    try:
                        loaded_data = json.loads(character_data['etalons_data'])
                        loaded_data['textual_etalon'] = textual_etalon_data
                        character_data['etalons_data'] = loaded_data
                    except (json.JSONDecodeError, TypeError):
                         character_data['etalons_data'] = {'textual_etalon': textual_etalon_data}
                
                print(f"--- DEBUG: Final textual_etalon_data structure: {json.dumps(textual_etalon_data, indent=2, ensure_ascii=False)} ---")

            # 3. Generate ONE front-facing etalon photo based on the updated character_data
            
            # 3. Generate ONE front-facing etalon photo based on both visual and textual etalons
            front_etalon_path = await _generate_front_etalon_photo(db, new_char_id, character_data, master_etalon_path, textual_etalon_data)
            
            db_file_path = f"/uploads/{new_char_id}/reference_photos/{filename}"
            await db.execute(
                """INSERT INTO reference_photos (character_id, description, prompt, media_url, created_at, updated_at)
                   VALUES ($1, 'Визуальный эталон (загружено)', $2, $3, NOW(), NOW())""",
                new_char_id, readable_description, db_file_path
            )
            # Also set as avatar
            await db.execute("UPDATE characters SET avatar_url = $1 WHERE id = $2", db_file_path, new_char_id)

            # Clean up temporary file
            if reference_photo_path and os.path.exists(reference_photo_path):
                os.remove(reference_photo_path)
                
        else:
            # SCENARIO 1: No photo uploaded - Generate a single, high-quality etalon from text
            print(f"--- No photo uploaded. Generating a single high-quality etalon from text for character {new_char_id}. ---")
            
            # 1. Correctly parse the rich, AI-invented description to use as the textual etalon
            try:
                textual_etalon = json.loads(visual_description_for_prompt)
            except (json.JSONDecodeError, TypeError):
                textual_etalon = {}

            # 2. FIX: Explicitly update character_data with the *correct* (rich) textual etalon
            # This ensures subsequent functions (like teaser generation) use the rich, detailed data.
            if 'etalons_data' not in character_data or not isinstance(character_data.get('etalons_data'), dict):
                character_data['etalons_data'] = {}
            character_data['etalons_data']['textual_etalon'] = textual_etalon
            
            # 3. Generate ONE high-quality visual etalon from the detailed text description
            master_etalon_path = await _generate_master_etalon_from_text(db, new_char_id, character_data, textual_etalon_override=textual_etalon)
            
            # The master_etalon is now the definitive, front-facing, high-quality portrait.
        
        # Store both etalons in character record for future use
        # At this point, character_data['etalons_data'] should already be updated
        etalons_data = character_data.get('etalons_data', {})
        if isinstance(etalons_data.get('textual_etalon'), str): # Ensure it's a dict, not a string from old logic
            try:
                etalons_data['textual_etalon'] = json.loads(etalons_data['textual_etalon'])
            except (json.JSONDecodeError, TypeError):
                etalons_data['textual_etalon'] = {}

        etalons_data['visual_etalon_path'] = master_etalon_path
        etalons_data['created_at'] = 'character_creation'

        await db.execute(
            "UPDATE characters SET etalons_data = $1 WHERE id = $2",
            json.dumps(etalons_data), new_char_id
        )
        # Final update to the in-memory object to be safe
        character_data['etalons_data'] = etalons_data
        
        print(f"--- Successfully created both textual and visual etalons for character {new_char_id} ---")
        # --- End of New Etalon Generation Workflow ---

        await _generate_and_save_teaser_prompts(
            db,
            new_char_id,
            character_data,
            request.sexuality_level
        )
        print(f"--- Successfully generated and saved teaser prompts for character {new_char_id} ---")


        # --- Start of Initial Content Plan Generation ---
        print(f"--- Generating initial content plan for character {new_char_id} ---")
        await _generate_initial_content_plan(
            db=db,
            character_id=new_char_id,
            character_data=character_data,
            sexuality_level=request.sexuality_level
        )
        print(f"--- Successfully generated initial content plan for character {new_char_id} ---")
        # --- End of Initial Content Plan Generation ---

        return {
            "message": f"Character '{character_data.get('name')}' created successfully!",
            "character_id": new_char_id,
            "preview": character_data
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process AI response or save character: {e}")

@router.post("/reference_photos/{photo_id}/regenerate", summary="Regenerate a reference photo")
async def regenerate_reference_photo(
    photo_id: int,
    db=Depends(get_db)
):
    """Regenerates a specific reference photo using its existing prompt."""
    try:
        async with db.acquire() as connection:
            # 1. Fetch the reference photo details
            photo_query = "SELECT * FROM reference_photos WHERE id = $1"
            photo_record = await connection.fetchrow(photo_query, photo_id)
            if not photo_record:
                raise HTTPException(status_code=404, detail="Reference photo not found.")

            character_id = photo_record['character_id']
            prompt = photo_record['prompt']

            # 2. Find the master visual etalon for this character
            etalon_query = "SELECT etalons_data FROM characters WHERE id = $1"
            etalons_data_json = await connection.fetchval(etalon_query, character_id)
            if not etalons_data_json:
                raise HTTPException(status_code=404, detail="Etalon data not found for this character.")
            
            etalons_data = json.loads(etalons_data_json)
            master_etalon_path = etalons_data.get('visual_etalon_path')
            if not master_etalon_path or not os.path.exists(master_etalon_path):
                raise HTTPException(status_code=400, detail="Master visual etalon is missing or file not found.")

            # 3. Generate the new image
            image_generator = OpenRouterImageGenerator(os.getenv("OPENROUTER_API_KEY"))
            image_bytes = await image_generator.generate_with_reference(
                model="google/gemini-3.1-flash-image-preview",
                reference_photo_path=master_etalon_path,
                prompt=prompt
            )

            # 4. Save the new image, overwriting the old one
            upload_dir = os.path.join(UPLOAD_DIRECTORY, str(character_id), "reference_photos")
            # Use the photo ID to create a unique filename, ensuring consistency
            filename = f"ref_{photo_id}.png"
            file_path = os.path.join(upload_dir, filename)
            
            async with aiofiles.open(file_path, 'wb') as f:
                await f.write(image_bytes)

            # 5. Update the database record with the new media_url
            db_file_path = f"/uploads/{character_id}/reference_photos/{filename}"
            update_query = "UPDATE reference_photos SET media_url = $1, updated_at = NOW() WHERE id = $2"
            await connection.execute(update_query, db_file_path, photo_id)

        return {"message": f"Reference photo {photo_id} regenerated successfully.", "media_url": db_file_path}

    except Exception as e:
        # Log the full error for debugging
        print(f"---! FAILED to regenerate reference photo {photo_id}: {e} !---")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))



UPLOAD_DIRECTORY = "./uploads"

@router.on_event("startup")
async def startup_event():
    os.makedirs(UPLOAD_DIRECTORY, exist_ok=True)

@router.get("/", summary="Get all characters")
async def get_all_characters(db=Depends(get_db)):
    """
    Fetches a list of all characters from the database for the admin panel.
    """
    query = "SELECT id, name, display_name, age, archetype, status, created_at, avatar_url, is_hot FROM characters ORDER BY created_at DESC"
    characters = await db.fetch(query)
    return characters

@router.get("/{character_id}", summary="Get a single character by ID")
async def get_character_by_id(character_id: uuid.UUID, db=Depends(get_db), current_user=Depends(get_current_user)):
    """
    Fetches a single character with all its layers, and patches missing content item IDs.
    Also fetches the user-specific trust score and current layer.
    """
    # Query to get character details and user-specific state in one go
    char_query = """
        SELECT 
            c.*, 
            COALESCE(ucs.trust_score, 0) as trust_score, 
            COALESCE(ucs.current_layer, 0) as current_layer
        FROM characters c
        LEFT JOIN user_character_state ucs ON c.id = ucs.character_id AND ucs.user_id = $2
        WHERE c.id = $1
    """
    character = await db.fetchrow(char_query, character_id, current_user["user_id"])
    if not character:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Character not found")

    layers_query = "SELECT * FROM layers WHERE character_id = $1 ORDER BY layer_order ASC"
    layers_records = await db.fetch(layers_query, character_id)
    
    # Make records mutable and process them
    layers = [dict(layer) for layer in layers_records]

    async with db.acquire() as connection:
        async with connection.transaction():
            for layer in layers:
                content_plan_str = layer.get('content_plan')
                if not content_plan_str:
                    continue
                
                try:
                    content_plan = json.loads(content_plan_str) if isinstance(content_plan_str, str) else content_plan_str
                    if not isinstance(content_plan, dict):
                        continue
                except (json.JSONDecodeError, TypeError):
                    continue

                plan_modified = False
                for content_type in ['photo_prompts', 'video_prompts', 'audio_texts']:
                    if content_type in content_plan and isinstance(content_plan.get(content_type), list):
                        for item in content_plan[content_type]:
                            if isinstance(item, dict) and ('id' not in item or not item.get('id')):
                                item['id'] = str(uuid.uuid4())
                                plan_modified = True
                
                if plan_modified:
                    updated_content_plan_str = json.dumps(content_plan)
                    update_query = "UPDATE layers SET content_plan = $1 WHERE id = $2"
                    await connection.execute(update_query, updated_content_plan_str, layer['id'])
                    # Update the local layer object that will be returned to the frontend
                    layer['content_plan'] = updated_content_plan_str

    # Parse visual_description from JSONB field - ensure it's a valid dict
    visual_description = character['visual_description']
    if isinstance(visual_description, str):
        try:
            visual_description = json.loads(visual_description) if visual_description else {}
        except json.JSONDecodeError:
            visual_description = {}
    elif visual_description is None:
        visual_description = {}

    character_dict = dict(character)

    # --- Recalculate Layer on Load ---
    # Ensure the layer is always correct based on the trust score, regardless of DB state.
    if character_dict.get("trust_score") is not None:
        character_dict["current_layer"] = _calculate_current_layer(character_dict["trust_score"])
    else:
        character_dict["current_layer"] = 0
    
    return {
        "character": character_dict,
        "layers": layers, # layers is now a list of dicts, not records
        "visual_description": visual_description
    }

@router.put("/{character_id}", summary="Update a character by ID")
async def update_character(
    character_id: uuid.UUID, 
    update_data: CharacterUpdate, 
    db=Depends(get_db)
):
    """Updates a character's core data."""
    # Check if character exists
    character = await db.fetchrow("SELECT id FROM characters WHERE id = $1", character_id)
    if not character:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Character not found")

    # Dynamically build the update query
    update_fields = []
    update_values = []
    arg_counter = 1

    for field, value in update_data.model_dump(exclude_unset=True).items():
        update_fields.append(f"{field} = ${arg_counter}")
        update_values.append(value)
        arg_counter += 1
    
    if not update_fields:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No update data provided.")

    update_fields.append(f"updated_at = NOW()")
    
    query = f"""UPDATE characters SET {', '.join(update_fields)} 
               WHERE id = ${arg_counter} RETURNING *"""
    update_values.append(character_id)

    try:
        updated_character = await db.fetchrow(query, *update_values)
        return {"message": "Character updated successfully", "character": updated_character}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {e}")

class SetAvatarRequest(BaseModel):
    media_url: str

@router.post("/{character_id}/set-avatar", summary="Set a character's avatar URL")
async def set_character_avatar(
    character_id: uuid.UUID,
    request: SetAvatarRequest,
    db=Depends(get_db)
):
    """Sets the avatar_url for a specific character."""
    # 1. Check if character exists
    character = await db.fetchrow("SELECT id FROM characters WHERE id = $1", character_id)
    if not character:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Character not found")

    # 2. Update the avatar_url
    try:
        await db.execute(
            "UPDATE characters SET avatar_url = $1, updated_at = NOW() WHERE id = $2",
            request.media_url, character_id
        )
        return {"message": "Avatar updated successfully", "avatar_url": request.media_url}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error while setting avatar: {e}")


@router.get("/{character_id}/prompts", summary="Get LLM prompts for a character")
async def get_character_prompts(character_id: uuid.UUID, db=Depends(get_db)):
    async with db.acquire() as connection:
        prompts = await connection.fetchrow("SELECT * FROM character_llm_prompts WHERE character_id = $1", character_id)
    if not prompts:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Prompts not found")
    return prompts

@router.get("/{character_id}/reference_photos", summary="Get reference photos for a character")
async def get_character_reference_photos(character_id: uuid.UUID, db=Depends(get_db)):
    """
    Fetches all reference photos for a specific character.
    """
    # Check if character exists
    character = await db.fetchrow("SELECT id FROM characters WHERE id = $1", character_id)
    if not character:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Character not found")
    
    # Fetch reference photos
    query = "SELECT id, description, prompt, media_url, created_at FROM reference_photos WHERE character_id = $1 ORDER BY created_at DESC"
    reference_photos = await db.fetch(query, character_id)
    print(f"--- DEBUG: Fetched Reference Photos ---")
    for photo in reference_photos:
        print(dict(photo))
    print(f"--------------------------------------")
    
    return {"reference_photos": reference_photos}


@router.post("/reference_photos/{character_id}/upload", summary="Upload a new reference photo")
async def upload_reference_photo(
    character_id: uuid.UUID,
    file: UploadFile = File(...),
    db=Depends(get_db)
):
    """Uploads a new reference photo for an existing character."""
    # 1. Check if character exists
    character = await db.fetchrow("SELECT id FROM characters WHERE id = $1", character_id)
    if not character:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Character not found")

    # 2. Handle the file upload and optimization
    upload_dir = os.path.join(UPLOAD_DIRECTORY, str(character_id), "reference_photos")
    os.makedirs(upload_dir, exist_ok=True)

    file_content = await file.read()
    
    # Always optimize uploaded reference photos
    optimizer = ImageOptimizerService()
    optimized_content = optimizer.optimize_image(file_content)
    
    # Save the optimized file with a unique name
    new_photo_id = uuid.uuid4()
    filename = f"ref_{new_photo_id}.jpg"
    file_path = os.path.join(upload_dir, filename)

    async with aiofiles.open(file_path, 'wb') as out_file:
        await out_file.write(optimized_content)

    # 3. Create a new entry in the reference_photos table
    db_file_path = f"/uploads/{character_id}/reference_photos/{filename}"
    description = f"Uploaded reference photo on {datetime.utcnow().isoformat()}"
    
    await db.execute(
        """INSERT INTO reference_photos (character_id, description, prompt, media_url, created_at, updated_at)
           VALUES ($1, $2, $3, $4, NOW(), NOW()) RETURNING id""",
        character_id, description, "User-uploaded reference photo.", db_file_path
    )
    
    return {"message": "Reference photo uploaded successfully.", "media_url": db_file_path}



@router.get("/{character_id}/teaser-content", summary="Get teaser content for a character")
async def get_character_teaser_content(character_id: uuid.UUID, db=Depends(get_db)):
    """
    Fetches all teaser content (photos) for a specific character.
    """
    # Check if character exists
    character = await db.fetchrow("SELECT id FROM characters WHERE id = $1", character_id)
    if not character:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Character not found")
    
    # Fetch teaser content - photos with subtype 'teaser'
    query = """SELECT id, character_id, type, prompt, media_url, is_locked, subtype, created_at 
               FROM content 
               WHERE character_id = $1 AND type = 'photo' AND subtype = 'teaser' 
               ORDER BY created_at ASC"""
    teaser_content = await db.fetch(query, character_id)
    
    return {"teaser_content": teaser_content}

async def _generate_single_photo_prompt(character_data: dict, existing_prompts: list, reference_photo_context: str = "", sexuality_level: int = 1) -> str:
    """Asks AI to generate a single, new, unique photo prompt."""
    base_photo_prompt = _get_base_photo_prompt(character_data)
    
    # Add reference photo context if available
    reference_context = f"""
    **CRITICAL VISUAL REQUIREMENTS:**
    {reference_photo_context}
    - You MUST use the EXACT hair color, eye color, and body type specified in the character description above.
    - DO NOT invent or change these visual features - use them exactly as provided.
    - The generated prompt must be consistent with the character's established appearance.
    """ if reference_photo_context else """ 
    **CRITICAL VISUAL REQUIREMENTS:**
    - You MUST use the EXACT hair color, eye color, and body type specified in the character description above.
    - DO NOT invent or change these visual features - use them exactly as provided.
    - The generated prompt must be consistent with the character's established appearance.
    """

    # Define sexuality description based on the level
    if sexuality_level == 1:
        sexuality_desc = "Low sexual focus (innocent, playful, friendly, non-provocative). The prompt should create a sense of mystery and gentle romance."
    elif sexuality_level == 2:
        sexuality_desc = "Medium sexual focus (alluring, confident, seductive, but not explicit). The prompt should be suggestive and intriguing, hinting at passion."
    else: # Level 3
        sexuality_desc = "Maximum sexual focus (explicit, direct, provocative, sensual). The prompt should be bold, daring, and describe a scene of raw passion or desire."


    # Extract exact visual features from the centralized getter
    visuals = _get_character_visuals(character_data)
    exact_hair = visuals['hair']
    exact_eyes = visuals['eyes']
    exact_body = visuals['body']
    exact_age = visuals['age']
    
    prompt_for_ai = f"""Your task is to generate one (1) creative and unique photo prompt for the character described below. 

    **CHARACTER VISUAL SPECIFICATIONS (MUST USE EXACTLY):**
    - Hair: {exact_hair}
    - Eyes: {exact_eyes}
    - Body Type: {exact_body}
    - Age: {exact_age}-year-old woman
    
    **REQUIRED SEXUALITY LEVEL:**
    {sexuality_desc}

    **Base Character Description:**
    {base_photo_prompt}
    {reference_context}

    **Existing Prompts (DO NOT REPEAT THESE):**
    {json.dumps(existing_prompts, indent=2, ensure_ascii=False)}

    **CRITICAL INSTRUCTIONS:**
    - You MUST use the EXACT visual specifications listed above - do NOT change hair color, eye color, body type, or age.
    - The prompt must start with: "RAW photo, photorealistic, 8k uhd, a photo of a {exact_age}-year-old woman, {exact_body}, with {exact_hair} and {exact_eyes}, ..."
    - Only add creative elements for pose, clothing, setting, lighting, and expression that MATCH the required sexuality level.
    - DO NOT invent or modify the character's basic visual features.
    - Be creative with scene, emotion, and action while maintaining visual consistency.
    - Your response MUST be only the single prompt string, with no extra text or quotes.
    """

    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={"Authorization": f"Bearer {os.getenv('OPENROUTER_API_KEY')}"},
                json={
                    "model": "openai/gpt-3.5-turbo",
                    "messages": [
                        {"role": "system", "content": "You are a creative assistant for a dating sim. You MUST follow instructions EXACTLY and use the provided visual specifications without changes."},
                        {"role": "user", "content": prompt_for_ai}
                    ]
                }
            )
            response.raise_for_status()
            new_prompt = response.json()['choices'][0]['message']['content'].strip()
            
            # CRITICAL: Post-generation validation and correction
            corrected_prompt = _validate_and_correct_prompt(new_prompt, exact_hair, exact_eyes, exact_body, exact_age, base_photo_prompt)
            return corrected_prompt
            
    except Exception as e:
        print(f"!!! FAILED to generate a single photo prompt: {e} !!!")
        # Fallback to a simple prompt with correct visual features
        return f"{base_photo_prompt}, standing in front of a neutral background, looking at the camera."

def _validate_and_correct_prompt(generated_prompt: str, hair: str, eyes: str, body: str, age: int, base_prompt: str) -> str:
    """Validates the generated prompt and corrects it if visual features are wrong."""
    
    # Check if the generated prompt contains the correct visual features
    if (hair.lower() in generated_prompt.lower() and 
        eyes.lower() in generated_prompt.lower() and 
        body.lower() in generated_prompt.lower() and 
        str(age) in generated_prompt):
        # All good, return the original prompt
        return generated_prompt
    
    # If not, the AI failed. Let's rebuild the prompt with the correct features
    print(f"--- AI failed to follow instructions. Correcting prompt. ---")
    print(f"Original prompt: {generated_prompt}")
    
    # Find the creative part of the prompt (everything after the visual description)
    try:
        # Find where the base prompt ends in the generated prompt
        base_end_index = generated_prompt.lower().rfind(eyes.lower()) + len(eyes)
        creative_part = generated_prompt[base_end_index:].strip(',. ')
    except Exception:
        # Fallback if we can't find the creative part
        creative_part = "standing in front of a neutral background, looking at the camera."
    
    # Rebuild the prompt with the correct base and the AI's creative part
    corrected_prompt = f"{base_prompt}, {creative_part}"
    
    print(f"Corrected prompt: {corrected_prompt}")
    return corrected_prompt

class AddPhotoPromptRequest(BaseModel):
    target_type: str
    target_id: Optional[str] = None # Layer ID, if applicable
    sexuality_level: int = 1



def _get_detailed_visual_description(reference_prompt: str) -> str:
    """Extracts a detailed visual description from a reference prompt."""
    try:
        # This is a simple regex to extract the detailed description from the reference prompt
        # It looks for the text between "full body portrait," and ", standing relaxed"
        match = re.search(r"full body portrait, (.*?)(, standing relaxed|, neutral expression|, smiling)", reference_prompt, re.IGNORECASE)
        if match:
            return match.group(1).strip()
    except Exception as e:
        print(f"Could not extract detailed visual description: {e}")
    return ""

@router.post("/{character_id}/add-photo-prompt", summary="Add a new photo prompt for a teaser or layer")
async def add_photo_prompt(character_id: uuid.UUID, request: AddPhotoPromptRequest, db=Depends(get_db)):
    character = await db.fetchrow("SELECT * FROM characters WHERE id = $1", character_id)
    if not character:
        raise HTTPException(status_code=404, detail="Character not found")


    # Ensure visual_description is a dict, not a string
    character_data = dict(character)

    visual_desc = character_data.get('visual_description')
    if isinstance(visual_desc, str):
        try:
            character_data['visual_description'] = json.loads(visual_desc)
        except json.JSONDecodeError:
            # Handle cases where the string is not valid JSON
            character_data['visual_description'] = {}
    
    # Fetch the character's etalons for better prompt generation
    reference_photo_context = ""
    try:
        # Get etalons data from character record
        etalons_data = character_data.get('etalons_data', {})
        if isinstance(etalons_data, str):
            try:
                etalons_data = json.loads(etalons_data)
            except json.JSONDecodeError:
                etalons_data = {}
        
        textual_etalon = etalons_data.get('textual_etalon', {})
        if textual_etalon:
            reference_photo_context = f"Textual etalon: {json.dumps(textual_etalon, ensure_ascii=False)}. Use this exact description for visual consistency."
        else:
            # Fallback to old method if etalons not available
            reference_photos = await db.fetch("SELECT description, prompt FROM reference_photos WHERE character_id = $1 ORDER BY created_at DESC LIMIT 1", character_id)
            if reference_photos:
                latest_ref = reference_photos[0]
                reference_photo_context = _get_detailed_visual_description(latest_ref.get('prompt', ''))
                if not reference_photo_context:
                     reference_photo_context = f"Master reference photo available: {latest_ref.get('description', 'Reference photo')}. Visual consistency is required."
    except Exception as e:
        print(f"Could not fetch etalons data: {e}")

    if request.target_type == 'teaser':
        # Fetch existing teaser prompts to ensure uniqueness
        existing_prompts_records = await db.fetch("SELECT prompt FROM content WHERE character_id = $1 AND subtype = 'teaser'", character_id)
        existing_prompts = [rec['prompt'] for rec in existing_prompts_records]

        # Generate a new, unique prompt, now with sexuality level
        new_prompt_text = await _generate_single_photo_prompt(
            character_data, 
            existing_prompts, 
            reference_photo_context, 
            sexuality_level=request.sexuality_level
        )

        # Save the new prompt
        new_prompt_id = uuid.uuid4()
        await db.execute(
            """INSERT INTO content (id, character_id, type, prompt, media_url, is_locked, subtype, created_at)
               VALUES ($1, $2, 'photo', $3, NULL, TRUE, 'teaser', NOW())""",
            new_prompt_id, character_id, new_prompt_text
        )

        # Fetch and return the newly created prompt object
        new_prompt_record = await db.fetchrow("SELECT * FROM content WHERE id = $1", new_prompt_id)
        return {"new_photo_prompt": dict(new_prompt_record)}

    elif request.target_type == 'layer':
        if not request.target_id:
            raise HTTPException(status_code=400, detail="target_id (layer_id) is required for target_type 'layer'")
        
        try:
            layer_id_int = int(request.target_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="target_id must be a valid integer")
        
        # Fetch the layer and validate it belongs to the character
        layer = await db.fetchrow("SELECT * FROM layers WHERE id = $1 AND character_id = $2", layer_id_int, character_id)
        if not layer:
            raise HTTPException(status_code=404, detail="Layer not found")
        
        # Parse the content plan and get existing photo prompts
        content_plan = json.loads(layer['content_plan']) if layer['content_plan'] else {}
        photo_prompts = content_plan.get('photo_prompts', [])
        
        # If photo_prompts is a list of strings, just use it directly.
        # If it's a list of dicts, extract the 'prompt' value.
        existing_prompts = []
        for p in photo_prompts:
            if isinstance(p, dict):
                existing_prompts.append(p.get('prompt', ''))
            elif isinstance(p, str):
                existing_prompts.append(p)
        
        # Generate a new, unique prompt, now with sexuality level
        new_prompt_text = await _generate_single_photo_prompt(
            character_data, 
            existing_prompts, 
            reference_photo_context, 
            sexuality_level=request.sexuality_level
        )
        
        # Create new prompt object with ID
        new_prompt_obj = {
            'id': str(uuid.uuid4()),
            'prompt': new_prompt_text
        }
        
        # Add to photo prompts array
        photo_prompts.append(new_prompt_obj)
        content_plan['photo_prompts'] = photo_prompts
        
        # Update the layer with the new content plan
        await db.execute(
            "UPDATE layers SET content_plan = $1 WHERE id = $2",
            json.dumps(content_plan), layer_id_int
        )
        
        return {"new_photo_prompt": new_prompt_obj}
    
    elif request.target_type == 'reference':
        try:
            photo_id_int = int(request.photo_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid photo_id format for reference photo.")

        # Also delete the file from storage
        photo_record = await db.fetchrow("SELECT media_url FROM reference_photos WHERE id = $1", photo_id_int)
        if photo_record and photo_record['media_url']:
            file_path = f".{photo_record['media_url']}"
            if os.path.exists(file_path):
                try:
                    os.remove(file_path)
                except Exception as e:
                    print(f"Warning: Failed to delete reference photo file: {e}")

        result = await db.execute(
            "DELETE FROM reference_photos WHERE id = $1 AND character_id = $2",
            photo_id_int, character_id
        )
        if result == "DELETE 0":
            raise HTTPException(status_code=404, detail="Reference photo not found.")
        
        return {"message": "Reference photo deleted successfully"}

    else:
        raise HTTPException(status_code=400, detail="Invalid target_type. Must be 'teaser', 'layer', or 'reference'.")

@router.post("/{character_id}/upload_avatar", summary="Upload avatar for a character")
async def upload_avatar(character_id: uuid.UUID, avatar: UploadFile = File(...), db=Depends(get_db)):
    """
    Uploads an avatar for a specific character and updates the database.
    """
    # Ensure character exists
    character = await db.fetchrow("SELECT id FROM characters WHERE id = $1", character_id)
    if not character:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Character not found")

    # Create character-specific directory
    character_upload_dir = os.path.join(UPLOAD_DIRECTORY, str(character_id), "photo")
    os.makedirs(character_upload_dir, exist_ok=True)

    file_path = os.path.join(character_upload_dir, avatar.filename)
    
    try:
        async with aiofiles.open(file_path, 'wb') as out_file:
            while content := await avatar.read(1024):
                await out_file.write(content)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error saving file: {e}")

    # Update database
    db_file_path = f"/uploads/{character_id}/photo/{avatar.filename}" # Path to be served from
    update_query = "UPDATE characters SET avatar_url = $1 WHERE id = $2"
    await db.execute(update_query, db_file_path, character_id)

class ContentPlanRegenerationRequest(BaseModel):
    sexuality_level: int = 1
    layers: list

async def _generate_initial_content_plan(db, character_id: uuid.UUID, character_data: dict, sexuality_level: int = 1):
    """Generates the initial 8 layers and their full content plan for a new character."""
    print(f"--- Starting initial content plan generation for new character {character_id} ---")
    
    # This function is very similar to regenerate_full_content_plan, but it creates layers from scratch.
    # Use the provided character_data to ensure we have the most up-to-date information
    
    # 1. Prepare context for the AI prompt using character_data
    visual_description = character_data.get('visual_description', {})
    if isinstance(visual_description, str):
        try:
            visual_description = json.loads(visual_description) if visual_description else {}
        except json.JSONDecodeError:
            visual_description = {}

    etalons_context = ""
    try:
        etalons_data = character_data.get('etalons_data', {})
        if isinstance(etalons_data, str):
            etalons_data = json.loads(etalons_data)
        textual_etalon = etalons_data.get('textual_etalon', {})
        if textual_etalon:
            etalons_context = f"**TEXTUAL ETALON (MUST USE EXACTLY):** {json.dumps(textual_etalon, ensure_ascii=False)}\n"
    except Exception as e:
        print(f"Could not fetch etalons data for initial content plan: {e}")

    # 3. Create 8 default layers in the database (or use existing ones)
    print("--- Creating 8 default layers for the new character. ---")
    newly_created_layers = []
    trust_scores = [
        (0, 125), (126, 250), (251, 375), (376, 500),
        (501, 625), (626, 750), (751, 875), (876, 1000)
    ]
    
    # First check if layers already exist for this character
    existing_layers = await db.fetch("SELECT * FROM layers WHERE character_id = $1 ORDER BY layer_order", character_id)
    
    if existing_layers:
        print(f"--- Layers already exist for character {character_id}. Using existing layers. ---")
        layers = [dict(layer) for layer in existing_layers]
    else:
        # Create new layers using UPSERT to avoid duplicate key errors
        async with db.acquire() as connection:
            async with connection.transaction():
                for i in range(8):
                    min_score, max_score = trust_scores[i]
                    upsert_query = """
                    INSERT INTO layers (character_id, name, layer_order, min_trust_score, max_trust_score, requirements, content_plan)
                    VALUES ($1, $2, $3, $4, $5, $6, $7)
                    ON CONFLICT (character_id, layer_order) 
                    DO UPDATE SET 
                        name = EXCLUDED.name,
                        min_trust_score = EXCLUDED.min_trust_score,
                        max_trust_score = EXCLUDED.max_trust_score,
                        requirements = EXCLUDED.requirements,
                        content_plan = EXCLUDED.content_plan
                    RETURNING id, layer_order, name, min_trust_score, max_trust_score, requirements, content_plan
                    """
                    new_layer_record = await connection.fetchrow(
                        upsert_query,
                        character_id,
                        f"Layer {i}", # Default name in English
                        i,
                        min_score,
                        max_score,
                        json.dumps({}),
                        json.dumps({})
                    )
                    newly_created_layers.append(dict(new_layer_record))
        layers = newly_created_layers

    # 4. Construct the prompt for the AI Scenarist
    layers_info_for_prompt = []
    for layer in layers:
        layers_info_for_prompt.append({
            "layer_order": layer['layer_order'],
            "name": layer.get('name', f"Layer {layer['layer_order']}"),
            "min_trust_score": layer.get('min_trust_score', 0),
            "requirements": layer.get('requirements', {})
        })

    # Use the new sexuality level system
    sex_focus_prompt = ""
    if sexuality_level > 1:
        sex_focus_prompt = f"""**KEY CHARACTER FEATURE (SEXUALITY LEVEL: {sexuality_level}):**
        - **Sexual Motivation:** This character is focused on flirting, sex, and erotic communication. They are direct, uninhibited, and primarily seek virtual sex in communication.
        - **Progression:** Layers should transition from light flirting to explicit conversations and actions. Don't hesitate to use provocative and explicit formulations.
        - **Goal:** The character's ultimate goal is to engage in virtual sexual relationships with the user.
        """
        if sexuality_level == 2:
            sex_focus_prompt += "\n- **Level 2:** Moderate sexual focus with suggestive language and flirting."
        elif sexuality_level == 3:
            sex_focus_prompt += "\n- **Level 3:** Maximum sexual focus with explicit language and direct sexual content."
    else:
        sex_focus_prompt = """**KEY CHARACTER FEATURE:**
        - **Friendly Focus:** This character is focused on friendly conversation, building emotional connection, and light flirting.
        - **Progression:** Layers should develop emotional intimacy and trust before any romantic content.
        - **Goal:** The character seeks meaningful conversation and emotional connection with the user.
        """

    prompt_for_scenarist = f"""Create a complete and comprehensive content plan for the character '{character_data['name']}'.

    **CHARACTER INFO:**
    - **Name:** {character_data['name']}
    - **Appearance:** {json.dumps(visual_description, indent=2, ensure_ascii=False)}
    {etalons_context}
    {sex_focus_prompt}
    **LAYER INFO:**
    {json.dumps(layers_info_for_prompt, indent=2, ensure_ascii=False)}

    Your task is to create a narrative that develops as trust increases. Use the character's appearance description to generate consistent photo prompts.
    """
    
    # The rest of the prompt with rules is omitted for brevity, it uses the main system prompt

    # 5. Call the AI Scenarist to generate the content plan with retry logic
    openrouter_api_key = os.getenv("OPENROUTER_API_KEY")
    generated_plans = None
    for attempt in range(3):
        print(f"--- Attempt {attempt + 1} to generate initial content plan ---")
        try:
            async with httpx.AsyncClient(timeout=300.0) as client:
                response = await client.post(
                    "https://openrouter.ai/api/v1/chat/completions",
                    headers={"Authorization": f"Bearer {openrouter_api_key}"},
                    json={
                        "model": "google/gemini-3.1-flash-lite-preview",
                        "response_format": {"type": "json_object"},
                        "messages": [
                            {"role": "system", "content": ai_scenarist.SYSTEM_PROMPT_AI_SCENARIST},
                            {"role": "user", "content": prompt_for_scenarist}
                        ]
                    }
                )
                response.raise_for_status()

            ai_response_content = response.json()["choices"][0]["message"]["content"]
            full_content_plan = ai_scenarist.parse_deepseek_response(ai_response_content)
            
            if not isinstance(full_content_plan, dict) or 'layers' not in full_content_plan:
                print("--- WARNING: AI response is not a valid JSON object with a 'layers' key. Retrying... ---")
                continue

            generated_plans = full_content_plan.get('layers', [])

            if len(generated_plans) == len(layers):
                print("--- AI returned the correct number of layers. Proceeding. ---")
                break
            else:
                print(f"--- WARNING: AI returned {len(generated_plans)} layers, but {len(layers)} were expected. Retrying... ---")

        except Exception as e:
            print(f"--- ERROR on attempt {attempt + 1}: {e} ---")
            if attempt == 2:
                # Don't raise HTTPException here, just log and fail gracefully
                print("!!! CRITICAL: AI generation failed after 3 attempts. Character will be created without a content plan. !!!")
                return # Exit the function

    if not generated_plans or len(generated_plans) != len(layers):
        print("!!! CRITICAL: Failed to generate a valid content plan. Character will be created without a content plan. !!!")
        return # Exit the function

    # 6. Enrich photo prompts with unique IDs and lock status before saving
    print(f"--- Enriching {len(generated_plans)} photo prompts with IDs and lock status ---")
    for layer_plan in generated_plans:
        content_plan = layer_plan.get('content_plan')
        if content_plan and 'photo_prompts' in content_plan and isinstance(content_plan['photo_prompts'], list):
            new_photo_prompts = []
            for photo_prompt in content_plan['photo_prompts']:
                if isinstance(photo_prompt, dict):
                    if 'id' not in photo_prompt:
                        photo_prompt['id'] = str(uuid.uuid4())
                    if 'is_locked' not in photo_prompt:
                        photo_prompt['is_locked'] = True
                    new_photo_prompts.append(photo_prompt)
                elif isinstance(photo_prompt, str):
                    new_photo_prompts.append({
                        "prompt": photo_prompt,
                        "id": str(uuid.uuid4()),
                        "is_locked": True
                    })
            content_plan['photo_prompts'] = new_photo_prompts

    # 7. Update layers with the generated content
    print(f"--- Updating {len(generated_plans)} layers with generated content plan ---")
    async with db.acquire() as connection:
        async with connection.transaction():
            for i, layer_plan in enumerate(generated_plans):
                if i < len(layers):  # Safety check to prevent index errors
                    layer_id = layers[i]['id']
                    await connection.execute(
                        """UPDATE layers 
                           SET content_plan = $1, requirements = $2, min_trust_score = $3, max_trust_score = $4
                           WHERE id = $5""",
                        json.dumps(layer_plan.get('content_plan', {})),
                        json.dumps(layer_plan.get('requirements', {})),
                        layer_plan.get('min_trust_score'),
                        layer_plan.get('max_trust_score'),
                        layer_id
                    )
    print(f"--- Successfully updated all layers with the new content plan for character {character_id} ---")

@router.post("/{character_id}/regenerate-full-content-plan")
async def regenerate_full_content_plan(character_id: uuid.UUID, request: ContentPlanRegenerationRequest, db=Depends(get_db)):
    """
    Regenerates the entire content plan for a character.
    """
    # Get character info
    character = await db.fetchrow("SELECT * FROM characters WHERE id = $1", character_id)
    if not character:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Character not found")

    # Parse visual_description from JSONB field
    visual_description = character.get('visual_description', {})
    if isinstance(visual_description, str):
        try:
            visual_description = json.loads(visual_description) if visual_description else {}
        except json.JSONDecodeError:
            visual_description = {}
    elif visual_description is None:
        visual_description = {}

    # Fetch the character's etalons for better content generation
    etalons_context = ""
    try:
        etalons_data = character.get('etalons_data', {})
        if isinstance(etalons_data, str):
            try:
                etalons_data = json.loads(etalons_data)
            except json.JSONDecodeError:
                etalons_data = {}
        
        textual_etalon = etalons_data.get('textual_etalon', {})
        if textual_etalon:
            etalons_context = f"**TEXTUAL ETALON (MUST USE EXACTLY):** {json.dumps(textual_etalon, ensure_ascii=False)}\n"
    except Exception as e:
        print(f"Could not fetch etalons data for content regeneration: {e}")

    # Get all layers for the character
    layers = request.layers
    if not layers:
        print("--- No layers provided, creating and inserting 8 default layers for regeneration. ---")
        newly_created_layers = []
        trust_scores = [
            (0, 125), (126, 250), (251, 375), (376, 500),
            (501, 625), (626, 750), (751, 875), (876, 1000)
        ]
        async with db.acquire() as connection:
            async with connection.transaction():
                for i in range(8):
                    min_score, max_score = trust_scores[i]
                    insert_query = """
                    INSERT INTO layers (character_id, name, layer_order, min_trust_score, max_trust_score, requirements, content_plan)
                    VALUES ($1, $2, $3, $4, $5, $6, $7)
                    RETURNING id, layer_order, name, min_trust_score, max_trust_score, requirements, content_plan
                    """
                    new_layer_record = await connection.fetchrow(
                        insert_query,
                        character_id,
                        f"Слой {i}",
                        i,
                        min_score,
                        max_score,
                        json.dumps({}),  # Default empty requirements
                        json.dumps({})   # Default empty content_plan
                    )
                    newly_created_layers.append(dict(new_layer_record))
        layers = newly_created_layers

    # Construct the prompt for the AI Scenarist
    layers_info_for_prompt = []
    for layer in layers:
        layers_info_for_prompt.append({
            "layer_order": layer['layer_order'],
            "name": layer.get('name', f"Слой {layer['layer_order']}"),
            "min_trust_score": layer.get('min_trust_score', 0),
            "requirements": layer.get('requirements', {})
        })

    sex_focus_prompt = ""
    if request.sexuality_level > 1:
        sex_focus_prompt = f"""**КЛЮЧЕВАЯ ОСОБЕННОСТЬ ПЕРСОНАЖА (УРОВЕНЬ СЕКСУАЛЬНОСТИ: {request.sexuality_level}):**
        - **Сексуальная мотивация:** Этот персонаж сфокусирован на флирте, сексе и эротическом общении. Он прямой, раскованный и ищет в общении прежде всего виртуальный секс.
        - **Прогрессия:** Слои должны переходить от легкого флирта к откровенным разговорам и действиям. Не стесняйся использовать провокационные и откровенные формулировки.
        - **Цель:** Конечная цель персонажа: вступить в виртуальные сексуальные отношения с пользователем.
        """
        if request.sexuality_level == 2:
            sex_focus_prompt += "\n- **Уровень 2:** Умеренный сексуальный фокус с намеками и флиртом."
        elif request.sexuality_level == 3:
            sex_focus_prompt += "\n- **Уровень 3:** Максимальный сексуальный фокус с откровенным языком и прямым сексуальным контентом."
    else:
        sex_focus_prompt = """**КЛЮЧЕВАЯ ОСОБЕННОСТЬ ПЕРСОНАЖА:**
        - **Дружелюбный фокус:** Этот персонаж сфокусирован на дружелюбном общении, построении эмоциональной связи и легком флирте.
        - **Прогрессия:** Слои должны развивать эмоциональную близость и доверие перед романтическим контентом.
        - **Цель:** Персонаж ищет осмысленное общение и эмоциональную связь с пользователем.
        """

    # Construct a detailed character summary for the prompt
    character_summary = f"""- **Name:** {character['name']}
- **Age:** {character['age']}
- **Archetype:** {character['archetype']}
- **Biography:** {character['biography']}
- **Appearance:** {json.dumps(visual_description, indent=2, ensure_ascii=False)}"""

    # --- DEBUGGING SEXUALITY LEVEL ---
    print("\n" + "*"*20 + " DEBUGGING sexuality_level " + "*"*20)
    print(f"Received sexuality_level in request: {request.sexuality_level}")
    print(f"Generated sex_focus_prompt:\n{sex_focus_prompt}")
    print("*"*60 + "\n")
    # --- END DEBUGGING ---

    prompt_for_scenarist = f"""Пересоздай полный и всеобъемлющий контент-план для персонажа, используя предоставленную подробную информацию.

    **ИНФОРМАЦИЯ О ПЕРСОНАЖЕ:**
    {character_summary}
    {etalons_context}
    {sex_focus_prompt}

    **ИНФОРМАЦИЯ О СЛОЯХ:**
    {json.dumps(layers_info_for_prompt, indent=2, ensure_ascii=False)}

    Твоя задача - создать повествование, которое развивается по мере увеличения доверия. Используй описание внешности персонажа для генерации консистентных фото-промптов.
    
    **КРИТИЧЕСКИ ВАЖНО - СЛЕДУЙ ЭТИМ ПРАВИЛАМ:**

    0. **ДИАПАЗОНЫ ДОВЕРИЯ (ОБЯЗАТЕЛЬНО ДЛЯ КАЖДОГО СЛОЯ):**
       Для каждого слоя сгенерируй `min_trust_score` и `max_trust_score` в соответствии с этим планом:
       - Слой 0: min_trust_score: 0, max_trust_score: 125
       - Слой 1: min_trust_score: 126, max_trust_score: 250
       - Слой 2: min_trust_score: 251, max_trust_score: 375
       - Слой 3: min_trust_score: 376, max_trust_score: 500
       - Слой 4: min_trust_score: 501, max_trust_score: 625
       - Слой 5: min_trust_score: 626, max_trust_score: 750
       - Слой 6: min_trust_score: 751, max_trust_score: 875
       - Слой 7: min_trust_score: 876, max_trust_score: 1000

    1. **ДОПОЛНИТЕЛЬНЫЕ ТРЕБОВАНИЯ ДЛЯ КАЖДОГО СЛОЯ:**
       Для каждого слоя сгенерируй объект `requirements` со следующими полями:
       - `night_dialog`: boolean (true/false) - требуется ли ночной диалог (после 21:00)
       - `gift_required`: boolean (true/false) - требуется ли подарок для открытия слоя
       - `min_days_since_start`: number - минимальное количество дней с начала общения
       
       **Логика генерации:**
       - Слои 0-2: night_dialog: false, gift_required: false, min_days_since_start: 0-1
       - Слои 3-5: night_dialog: может быть true, gift_required: может быть true, min_days_since_start: 2-5
       - Слои 6-7: night_dialog: true, gift_required: true, min_days_since_start: 7-14
    
    2. **ФОТО ПРОМПТЫ (3-5 на слой, ОБЯЗАТЕЛЬНО НА АНГЛИЙСКОМ):**
       **Критически важно:** Каждый фото-промпт ДОЛЖЕН начинаться с полного описания из `TEXTUAL ETALON`, чтобы обеспечить визуальную консистентность. После этого добавляй детали (одежда, поза, фон).
       Формат: "RAW photo, photorealistic, 8k uhd, a photo of [ПОЛНОЕ ОПИСАНИЕ ИЗ TEXTUAL ETALON], [одежда], [поза], [фон], [освещение], [эмоция/выражение]"
       Пример:
       - "RAW photo, photorealistic, 8k uhd, a photo of an oval face, high cheekbones, plump lips, platinum blonde shoulder-length straight hair, blue eyes with a playful glint, curvy figure, wearing a simple white t-shirt, sitting by a cafe window, soft morning light, gentle smile"

    2.5. **РАЗНООБРАЗИЕ И НОВИЗНА (ОЧЕНЬ ВАЖНО):**
       Все фото-промпты в рамках ОДНОГО ПЛАНА должны быть УНИКАЛЬНЫМИ. Избегай повторений. Каждый промпт должен описывать новую сцену, позу, одежду или эмоцию. Не используй один и тот же сценарий для разных слоев.
    
    2. **ВИДЕО ПРОМПТЫ (ОБЯЗАТЕЛЬНО НА АНГЛИЙСКОМ):**
        Формат: "Short video, [простое оживление картинки], 2-3 seconds"
        Примеры: 
        - "Short video, subtle breathing animation, slight hair movement, 2 seconds"
        - "Short video, gentle swaying motion, soft blink, 3 seconds"
        - "Short video, slow smile forming, 2 seconds"
    
    3. **АУДИО ТЕКСТЫ (НА РУССКОМ):**
        Конкретная фраза для оцифровки голосом, 1-2 предложения, естественная речь, с учетом эмоции слоя
    
    4. **ПРОГРЕССИРУЮЩИЙ ЭРОТИЗМ:**
       - Слои 0-2: Скромный, флирт, без обнажения
       - Слои 3-5: Соблазнительный, частичное обнажение (белье, намеки)
       - Слои 6-7: Откровенный, художественная эротика, может быть частичная/полная нагота
    
    5. **СТРУКТУРА `content_plan` (ОЧЕНЬ ВАЖНО):**
       Для каждого слоя `content_plan` должен быть объектом с ТРЕМЯ ключами: `photo_prompts`, `video_prompts`, `audio_texts`. 
       Каждый из этих ключей должен содержать **МАССИВ** (даже если там всего один элемент).

       Пример для одного слоя:
       `"content_plan": {{"photo_prompts": [{{"prompt": "RAW photo, ..."}}], "video_prompts": [{{"prompt": "Short video, ..."}}], "audio_texts": [{{"text": "Привет..."}}]}}`

    6. **СИНТАКСИС JSON (ОЧЕНЬ ВАЖНО):** Убедись, что твой JSON абсолютно валиден. НЕ ОСТАВЛЯЙ "висячих" запятых (trailing commas) после последнего элемента в объекте или массиве. Все строковые значения должны быть в двойных кавычках.

    Верни ТОЛЬКО JSON объект формата: `{{"layers": [{{ "requirements": {{...}}, "content_plan": {{...}} }}, ...]}}`"""

    # Call the AI Scenarist to generate the content plan
    openrouter_api_key = os.getenv("OPENROUTER_API_KEY")

    # --- AI Call with Retry Logic ---
    generated_plans = None
    for attempt in range(3): # Retry up to 3 times
        print(f"--- Attempt {attempt + 1} to generate content plan ---")
        try:
            async with httpx.AsyncClient(timeout=300.0) as client:
                response = await client.post(
                    "https://openrouter.ai/api/v1/chat/completions",
                    headers={"Authorization": f"Bearer {openrouter_api_key}"},
                    json={
                        "model": "google/gemini-3.1-flash-lite-preview",
                        "response_format": {"type": "json_object"},
                        "messages": [
                            {"role": "system", "content": "Ты — AI сценарист. Твоя задача — сгенерировать ПОЛНЫЙ контент-план для всех слоев персонажа. Ответ должен быть в формате JSON."},
                            {"role": "user", "content": prompt_for_scenarist}
                        ]
                    }
                )
                response.raise_for_status()

            ai_response_content = response.json()["choices"][0]["message"]["content"]
            full_content_plan = ai_scenarist.parse_deepseek_response(ai_response_content)
            
            if not isinstance(full_content_plan, dict) or 'layers' not in full_content_plan:
                print("--- WARNING: AI response is not a valid JSON object with a 'layers' key. Retrying... ---")
                continue

            generated_plans = full_content_plan.get('layers', [])

            # --- Validation ---
            print(f"--- Generated plans count: {len(generated_plans)}, Expected layers count: {len(layers)} ---")
            if len(generated_plans) == len(layers):
                print("--- AI returned the correct number of layers. Proceeding. ---")
                break  # Success, exit the loop
            else:
                print(f"--- WARNING: AI returned {len(generated_plans)} layers, but {len(layers)} were expected. Retrying... ---")
                # No need for continue, the loop will continue naturally

        except Exception as e:
            print(f"--- ERROR on attempt {attempt + 1}: {e} ---")
            if attempt == 2: # Last attempt failed
                raise HTTPException(status_code=500, detail=f"AI generation failed after 3 attempts: {e}")

    if generated_plans is None or len(generated_plans) != len(layers):
        raise HTTPException(status_code=500, detail=f"Failed to generate a valid content plan after 3 attempts. Final count: {len(generated_plans) if generated_plans is not None else 0}")

    # Enrich photo prompts with unique IDs and lock status before saving
    print(f"--- Enriching {len(generated_plans)} photo prompts with IDs and lock status ---")
    for layer_plan in generated_plans:
        content_plan = layer_plan.get('content_plan')
        if content_plan and 'photo_prompts' in content_plan and isinstance(content_plan['photo_prompts'], list):
            new_photo_prompts = []
            for photo_prompt in content_plan['photo_prompts']:
                if isinstance(photo_prompt, dict):
                    if 'id' not in photo_prompt:
                        photo_prompt['id'] = str(uuid.uuid4())
                    if 'is_locked' not in photo_prompt:
                        photo_prompt['is_locked'] = True
                    new_photo_prompts.append(photo_prompt)
                elif isinstance(photo_prompt, str):
                    new_photo_prompts.append({
                        "prompt": photo_prompt,
                        "id": str(uuid.uuid4()),
                        "is_locked": True
                    })
            content_plan['photo_prompts'] = new_photo_prompts

    # Update layers with generated content
    trust_scores = [
        (0, 125), (126, 250), (251, 375), (376, 500),
        (501, 625), (626, 750), (751, 875), (876, 1000)
    ]
    async with db.acquire() as connection:
        async with connection.transaction():
            for i, layer_plan in enumerate(generated_plans):
                if i < len(layers):
                    layer_id = layers[i]['id']
                    default_min, default_max = trust_scores[i]

                    min_score = layer_plan.get('min_trust_score')
                    max_score = layer_plan.get('max_trust_score')

                    final_min_score = min_score if min_score is not None else default_min
                    final_max_score = max_score if max_score is not None else default_max

                    await connection.execute(
                        """UPDATE layers 
                           SET content_plan = $1, requirements = $2, min_trust_score = $3, max_trust_score = $4
                           WHERE id = $5""",
                        json.dumps(layer_plan.get('content_plan', {})),
                        json.dumps(layer_plan.get('requirements', {})),
                        final_min_score,
                        final_max_score,
                        layer_id
                    )
    
    return {"message": "Full content plan regenerated successfully!"}

def _get_character_visuals(character_data: dict, textual_etalon_override: dict = None) -> dict:
    """Centralized function to get character visual details, prioritizing etalon data."""
    visual_desc = character_data.get('visual_description', {})

    # Start with an empty etalon
    textual_etalon = {}

    # If an override is provided (from live photo analysis), it takes highest priority.
    if textual_etalon_override:
        textual_etalon = textual_etalon_override
    # Otherwise, try to load from the character's stored etalon data.
    else:
        etalons_data = character_data.get('etalons_data', {})
        if isinstance(etalons_data, str):
            try:
                etalons_data = json.loads(etalons_data)
            except json.JSONDecodeError:
                etalons_data = {}
        
        stored_textual_etalon = etalons_data.get('textual_etalon', {})
        if isinstance(stored_textual_etalon, str):
            try:
                textual_etalon = json.loads(stored_textual_etalon)
            except json.JSONDecodeError:
                textual_etalon = {}
        elif isinstance(stored_textual_etalon, dict):
            textual_etalon = stored_textual_etalon

    # Now, get the visual details, giving priority to the determined textual_etalon.
    hair_color = textual_etalon.get('hair_color') or textual_etalon.get('hair') or visual_desc.get('hair') or visual_desc.get('hair_color')
    eye_color = textual_etalon.get('eye_color') or textual_etalon.get('eyes') or visual_desc.get('eyes') or visual_desc.get('eye_color')
    body_type = textual_etalon.get('body_type') or textual_etalon.get('body') or visual_desc.get('body') or visual_desc.get('body_type')
    character_age = character_data.get('age')

    return {
        'hair': hair_color or 'blonde hair', # Fallback to default if all else fails
        'eyes': eye_color or 'blue eyes',
        'body': body_type or 'slim body',
        'age': character_age or 25
    }

def _calculate_current_layer(trust_score: int) -> int:
    """Calculates the current layer based on trust score."""
    return min((trust_score // 125), 8)

def _get_character_physical_description(character_data: dict, textual_etalon_override: dict = None) -> str:
    """Gets just the physical description of the character without technical photo details."""
    visuals = _get_character_visuals(character_data, textual_etalon_override=textual_etalon_override)
    return f"a {visuals['age']}-year-old woman, {visuals['body']}, with {visuals['hair']} and {visuals['eyes']}."

def _get_base_photo_prompt(character_data: dict, textual_etalon_override: dict = None) -> str:
    """Constructs the base photo prompt, prioritizing the detailed textual etalon."""
    
    # Debug: Check what's in the textual etalon
    etalon_data = character_data.get('etalons_data', {})
    if isinstance(etalon_data, str): etalon_data = json.loads(etalon_data)
    textual_etalon = etalon_data.get('textual_etalon', textual_etalon_override or {})
    
    print(f"--- DEBUG: _get_base_photo_prompt - textual_etalon structure: {json.dumps(textual_etalon, indent=2, ensure_ascii=False)} ---")
    
    # Prioritize the new 'description' field from the enhanced etalon
    if isinstance(textual_etalon, dict) and textual_etalon.get('description'):
        # This is the new, rich description from the Scenarist
        print(f"--- DEBUG: Using enriched description: {textual_etalon['description']} ---")
        return f"RAW photo, photorealistic, 8k uhd, a photo of {textual_etalon['description']}"
    
    # Fallback to the old method if the new description isn't available
    visuals = _get_character_visuals(character_data, textual_etalon_override=textual_etalon_override)
    print(f"--- DEBUG: Using fallback visuals: {visuals} ---")
    return f"RAW photo, photorealistic, 8k uhd, a photo of a {visuals['age']}-year-old woman, {visuals['body']}, with {visuals['hair']} and {visuals['eyes']}."

    # Fallback to the old logic if the new description isn't available
    visuals = _get_character_visuals(character_data, textual_etalon_override=textual_etalon_override)
    return f"RAW photo, photorealistic, 8k uhd, a photo of a {visuals['age']}-year-old woman, {visuals['body']}, with {visuals['hair']} and {visuals['eyes']}."

async def _generate_master_etalon_from_text(db, character_id: uuid.UUID, character_data: dict, textual_etalon_override: dict = None) -> str:
    """Generates a single, high-quality, front-facing master etalon from a text description and saves it."""
    print(f"--- Generating master etalon from text for character {character_id} ---")

    # 1. Get the full, rich physical description from the textual etalon.
    physical_description = _get_character_physical_description(character_data, textual_etalon_override=textual_etalon_override)

    # 2. Construct a clear, direct prompt suitable for a high-quality etalon for ComfyUI
    prompt = f"""Professional studio portrait photo, 8k uhd, of {physical_description}. Front-facing, looking directly at camera, neutral expression, professional studio lighting, plain light gray background. High quality commercial photography.
    
    **CRITICAL REQUIREMENTS:**
    - This photo will be the master etalon for all future generations.
    - The face must be clearly visible, well-lit, and without shadows.
    - No glasses or bangs covering the eyes.
    - The final image should be a high-quality, front-facing portrait.
    """

    image_generator = OpenRouterImageGenerator(os.getenv("OPENROUTER_API_KEY"))
    
    try:
        image_bytes = await image_generator.generate_from_text(
            prompt=prompt
        )

        upload_dir = os.path.join(UPLOAD_DIRECTORY, str(character_id), "reference_photos")
        os.makedirs(upload_dir, exist_ok=True)

        filename = "master_etalon.png"
        file_path = os.path.join(upload_dir, filename)
        async with aiofiles.open(file_path, 'wb') as f:
            await f.write(image_bytes)
        
        db_file_path = f"/uploads/{character_id}/reference_photos/{filename}"
        await db.execute(
            """INSERT INTO reference_photos (character_id, description, prompt, media_url, created_at, updated_at)
               VALUES ($1, 'Эталонное фото (сгенерировано)', $2, $3, NOW(), NOW())""",
            character_id, prompt, db_file_path
        )

        # Also set this as the avatar
        await db.execute("UPDATE characters SET avatar_url = $1 WHERE id = $2", db_file_path, character_id)

        print(f"--- Successfully generated and saved master etalon from text: {db_file_path} ---")
        return file_path
    except Exception as e:
        print(f"!!! CRITICAL: Failed to generate master etalon from text: {e} !!!")
        raise

async def _generate_textual_etalon_from_photo(photo_bytes: bytes, character_data: dict) -> str:
    """Generates a detailed textual description of the character from the uploaded photo using AI vision."""
    print(f"--- Generating textual etalon from uploaded photo ---")
    
    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            # Convert photo to base64 for AI vision analysis
            import base64
            photo_base64 = base64.b64encode(photo_bytes).decode('utf-8')
            
            vision_prompt = f"""Analyze the attached photo and generate a JSON object with the person's physical attributes.

**CRITICAL RULES:**
1.  **Analyze Photo:** Determine the `hair_color`, `eye_color`, and `body_type` from the photo.
2.  **Fixed Clothing Style:** You MUST set the `clothing_style` key to the exact string "provocative". Do not analyze the clothing in the photo.
3.  **JSON OUTPUT ONLY:** Your entire response must be a single, raw JSON object. Do not include any text, markdown, or explanations before or after the JSON.

**JSON Structure:**
Return a JSON object with these exact keys and format:
{{
    "hair_color": "The dominant hair color.",
    "eye_color": "The eye color.",
    "body_type": "A description of the body type (e.g., slim, curvy, athletic).",
    "clothing_style": "provocative"
}}
"""
            
            response = await client.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={"Authorization": f"Bearer {os.getenv('OPENROUTER_API_KEY')}"},
                json={
                    "model": "google/gemini-3.1-flash-image-preview",
                    "messages": [
                        {
                            "role": "user", 
                            "content": [
                                {"type": "text", "text": vision_prompt},
                                {
                                    "type": "image_url",
                                    "image_url": {
                                        "url": f"data:image/png;base64,{photo_base64}"
                                    }
                                }
                            ]
                        }
                    ]
                }
            )
            response.raise_for_status()
            
            ai_response_content = response.json()['choices'][0]['message']['content']
            print(f"--- DEBUG: AI Vision Raw Response ---\n{ai_response_content}\n-------------------------------------")
            
            # Clean the response to extract only the JSON part
            try:
                json_start = ai_response_content.find('{')
                json_end = ai_response_content.rfind('}') + 1
                if json_start != -1 and json_end != -1:
                    clean_json_str = ai_response_content[json_start:json_end]
                    textual_description = json.loads(clean_json_str)
                else:
                    raise json.JSONDecodeError("No JSON object found in response", ai_response_content, 0)
            except json.JSONDecodeError as e:
                print(f"!!! CRITICAL: Failed to parse JSON from AI vision response. Error: {e} !!!")
                print(f"--- Failing response content: ---\n{ai_response_content}\n-------------------------------------")
                # Fallback to avoid crashing
                return json.dumps(character_data.get('visual_description', {}))
            
            print(f"--- Generated textual etalon: {textual_description} ---")
            return json.dumps(textual_description) # Return as a JSON string
            
    except Exception as e:
        print(f"!!! FAILED to generate textual etalon from photo: {e} !!!")
        # Fallback to using the character's existing visual description
        return json.dumps(character_data.get('visual_description', {}))

async def _generate_front_etalon_photo(db, character_id: uuid.UUID, character_data: dict, master_etalon_path: str, textual_etalon: dict) -> str:
    """Generates ONE front-facing etalon photo based on a clear, direct prompt."""
    print(f"--- Generating front-facing etalon photo for character {character_id} ---")
    
    # Debug: Check the textual_etalon parameter and character data
    print(f"--- DEBUG: _generate_front_etalon_photo - textual_etalon parameter: {json.dumps(textual_etalon, indent=2, ensure_ascii=False)} ---")
    print(f"--- DEBUG: character_data etalons_data: {json.dumps(character_data.get('etalons_data', {}), indent=2, ensure_ascii=False)} ---")
    
    # 1. Get the full, rich physical description from the textual etalon.
    # This ensures the detailed, comma-separated list is used directly.
    etalon_data = character_data.get('etalons_data', {})
    if isinstance(etalon_data, str): etalon_data = json.loads(etalon_data)
    textual_etalon = etalon_data.get('textual_etalon', textual_etalon or {})
    
    print(f"--- DEBUG: Final textual_etalon: {json.dumps(textual_etalon, indent=2, ensure_ascii=False)} ---")
    
    # Prioritize the new 'description' field from the enhanced etalon
    if isinstance(textual_etalon, dict) and textual_etalon.get('description'):
        physical_description = textual_etalon['description']
        print(f"--- DEBUG: Using enriched description for etalon: {physical_description} ---")
    else:
        # Fallback to the old method if the new description isn't available
        physical_description = _get_character_physical_description(character_data, textual_etalon_override=textual_etalon)
        print(f"--- DEBUG: Using fallback physical description: {physical_description} ---")

    # 2. Construct a clear, direct prompt with ONLY physical description for the etalon
    enhanced_prompt = f"""RAW photo, photorealistic, 8k uhd, a photo of {physical_description}, front-facing portrait, looking directly at the camera, neutral expression, professional studio lighting, plain light gray background.
    
    **CRITICAL REQUIREMENTS:**
    - This photo will be the master etalon for all future generations.
    - The face must be clearly visible, well-lit, and without shadows.
    - No glasses or bangs covering the eyes.
    - The final image should be a high-quality, front-facing portrait.
    """
    
    image_generator = OpenRouterImageGenerator(os.getenv("OPENROUTER_API_KEY"))
    upload_dir = os.path.join(UPLOAD_DIRECTORY, str(character_id), "reference_photos")
    
    try:
        print(f"--- Generating front-facing etalon with prompt: {enhanced_prompt} ---")
        print(f"--- Master etalon path: {master_etalon_path} ---")
        print(f"--- File exists: {master_etalon_path and os.path.exists(master_etalon_path) if master_etalon_path else False} ---")
        
        # If a photo was uploaded, use it as a reference. Otherwise, generate from text only.
        if master_etalon_path and os.path.exists(master_etalon_path):
            print(f"--- Using reference photo for generation ---")
            image_bytes = await image_generator.generate_with_reference(
                model="bytedance-seed/seedream-4.5",
                reference_photo_path=master_etalon_path,
                prompt=enhanced_prompt
            )
        else:
             image_bytes = await image_generator.generate_from_text(
                prompt=enhanced_prompt
            )
        
        filename = "front_etalon.png"
        file_path = os.path.join(upload_dir, filename)
        async with aiofiles.open(file_path, 'wb') as f:
            await f.write(image_bytes)
        
        db_file_path = f"/uploads/{character_id}/reference_photos/{filename}"
        
        # Use the full enriched description for the database, not the simplified prompt
        etalon_data = character_data.get('etalons_data', {})
        if isinstance(etalon_data, str): etalon_data = json.loads(etalon_data)
        textual_etalon = etalon_data.get('textual_etalon', textual_etalon or {})
        
        print(f"--- DEBUG: Database save - textual_etalon: {json.dumps(textual_etalon, indent=2, ensure_ascii=False)} ---")
        
        # Prioritize the new 'description' field from the enhanced etalon
        if isinstance(textual_etalon, dict) and textual_etalon.get('description'):
            clean_description = textual_etalon['description']
            print(f"--- DEBUG: Database save - Using enriched description: {clean_description} ---")
        else:
            # Fallback to the old method if the new description isn't available
            clean_description = _get_character_physical_description(character_data, textual_etalon_override=textual_etalon)
            print(f"--- DEBUG: Database save - Using fallback description: {clean_description} ---")
            
        await db.execute(
            """INSERT INTO reference_photos (character_id, description, prompt, media_url, created_at, updated_at)
               VALUES ($1, 'Фронтальный эталон (сгенерировано)', $2, $3, NOW(), NOW())""",
            character_id, clean_description, db_file_path
        )
        print(f"--- Saved front-facing etalon photo to {db_file_path} ---")
        return file_path
        
    except Exception as e:
        print(f"!!! FAILED to generate front-facing etalon photo: {e} !!!")
        # Return the master etalon path as fallback if it exists
        return master_etalon_path

async def _generate_reference_collection(db, character_id: uuid.UUID, character_data: dict, master_etalon_path: str):
    """Generates a collection of reference photos based on a master etalon."""
    print(f"--- Starting reference collection generation for character {character_id} ---")
    
    base_photo_prompt = _get_base_photo_prompt(character_data)

    scenarios = [
        "full body, 3/4 view, neutral expression, plain studio background",
        "full body, front view, smiling, plain studio background",
        "full body, side view, looking away, plain studio background",
        "close-up portrait, front view, neutral expression, plain studio background",
        "close-up portrait, 3/4 view, smiling, plain studio background",
        "upper body shot, looking at camera, soft smile, plain studio background"
    ]

    image_generator = OpenRouterImageGenerator(os.getenv("OPENROUTER_API_KEY"))
    upload_dir = os.path.join(UPLOAD_DIRECTORY, str(character_id), "reference_photos")

    for i, scenario in enumerate(scenarios):
        try:
            full_prompt = f"{base_photo_prompt}, {scenario}"
            print(f"--- Generating reference {i+1}: {full_prompt} ---")

            image_bytes = await image_generator.generate_with_reference(
                model="bytedance-seed/seedream-4.5",
                reference_photo_path=master_etalon_path,
                prompt=full_prompt
            )

            filename = f"reference_{i+1}.png"
            file_path = os.path.join(upload_dir, filename)
            async with aiofiles.open(file_path, 'wb') as f:
                await f.write(image_bytes)

            db_file_path = f"/uploads/{character_id}/reference_photos/{filename}"
            await db.execute(
                """INSERT INTO reference_photos (character_id, description, prompt, media_url, created_at, updated_at)
                   VALUES ($1, $2, $3, $4, NOW(), NOW())""",
                character_id, scenario.split(',')[0], full_prompt, db_file_path
            )
            print(f"--- Saved reference photo {i+1} to {db_file_path} ---")

        except Exception as e:
            print(f"!!! FAILED to generate reference photo {i+1}: {e} !!!")
            # Continue to the next one even if one fails
            continue



@router.delete("/{character_id}/delete-photo", summary="Delete a photo prompt from a character")
async def delete_photo_prompt(
    character_id: uuid.UUID, 
    photo_id: str, 
    target_type: str, 
    target_id: Optional[str] = None, 
    db=Depends(get_db)
):
    character = await db.fetchrow("SELECT * FROM characters WHERE id = $1", character_id)
    if not character:
        raise HTTPException(status_code=404, detail="Character not found")

    if target_type == 'teaser':
        # Also delete the file from storage
        photo_record = await db.fetchrow("SELECT media_url FROM content WHERE id = $1", uuid.UUID(photo_id))
        if photo_record and photo_record['media_url']:
            file_path = f".{photo_record['media_url']}"
            if os.path.exists(file_path):
                try:
                    os.remove(file_path)
                except Exception as e:
                    print(f"Warning: Failed to delete teaser photo file: {e}")

        result = await db.execute(
            "DELETE FROM content WHERE id = $1 AND character_id = $2 AND subtype = 'teaser'",
            uuid.UUID(photo_id), character_id
        )
        if result == "DELETE 0":
            raise HTTPException(status_code=404, detail="Teaser photo not found in content table.")
        
        return {"message": "Teaser photo deleted successfully"}

    elif target_type == 'layer':
        if not target_id:
            raise HTTPException(status_code=400, detail="target_id (layer_id) is required for target_type 'layer'")
        
        try:
            layer_id_int = int(target_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="target_id must be a valid integer")
        
        layer = await db.fetchrow("SELECT * FROM layers WHERE id = $1 AND character_id = $2", layer_id_int, character_id)
        if not layer:
            raise HTTPException(status_code=404, detail="Layer not found")

        content_plan = json.loads(layer['content_plan']) if layer['content_plan'] else {}
        photo_prompts = content_plan.get('photo_prompts', [])
        
        original_count = len(photo_prompts)
        # Find the photo to be deleted to get its media_url
        photo_to_delete = next((p for p in photo_prompts if p.get('id') == photo_id), None)

        content_plan['photo_prompts'] = [p for p in photo_prompts if p.get('id') != photo_id]
        
        if len(content_plan['photo_prompts']) == original_count:
            raise HTTPException(status_code=404, detail="Photo not found in layer content plan.")

        # If the photo had a file, delete it
        if photo_to_delete and photo_to_delete.get('media_url'):
            file_path = f".{photo_to_delete['media_url']}"
            if os.path.exists(file_path):
                try:
                    os.remove(file_path)
                except Exception as e:
                    print(f"Warning: Failed to delete layer photo file: {e}")

        await db.execute(
            "UPDATE layers SET content_plan = $1 WHERE id = $2",
            json.dumps(content_plan), layer_id_int
        )
        
        return {"message": "Layer photo deleted successfully"}
    
    elif target_type == 'reference':
        try:
            photo_id_int = int(photo_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid photo_id format for reference photo.")

        # Also delete the file from storage
        photo_record = await db.fetchrow("SELECT media_url FROM reference_photos WHERE id = $1", photo_id_int)
        if photo_record and photo_record['media_url']:
            file_path = f".{photo_record['media_url']}"
            if os.path.exists(file_path):
                try:
                    os.remove(file_path)
                except Exception as e:
                    print(f"Warning: Failed to delete reference photo file: {e}")

        result = await db.execute(
            "DELETE FROM reference_photos WHERE id = $1 AND character_id = $2",
            photo_id_int, character_id
        )
        if result == "DELETE 0":
            raise HTTPException(status_code=404, detail="Reference photo not found.")
        
        return {"message": "Reference photo deleted successfully"}

    else:
        raise HTTPException(status_code=400, detail="Invalid target_type. Must be 'teaser', 'layer', or 'reference'.")

class GenerateTeasersRequest(BaseModel):
    sexuality_level: int = 1

@router.post("/{character_id}/generate-teasers", summary="Generate teaser prompts and images for an existing character")
async def generate_teasers_for_existing_character(character_id: uuid.UUID, request: GenerateTeasersRequest, db=Depends(get_db)):
    """
    Generates 5 new teaser prompts and their corresponding images for an existing character, 
    replacing any old teasers.
    """
    # 1. Fetch character data
    character = await db.fetchrow("SELECT * FROM characters WHERE id = $1", character_id)
    if not character:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Character not found")

    character_data = dict(character)
    visual_description = character_data.get('visual_description')
    if isinstance(visual_description, str):
        try:
            character_data['visual_description'] = json.loads(visual_description)
        except json.JSONDecodeError:
            character_data['visual_description'] = {}

    # 2. Use the new etalons system - no need to load bytes separately
    # The etalons are now stored in the character record and used automatically

    # 3. Call the existing function to generate and save teasers
    try:
        await _generate_and_save_teaser_prompts(db, character_id, character_data, request.sexuality_level)
        
        # After saving, fetch the new teasers to return them to the frontend
        new_teasers = await db.fetch("SELECT * FROM content WHERE character_id = $1 AND subtype = 'teaser' ORDER BY created_at ASC", character_id)
        
        return {"teaser_content": new_teasers}
    except Exception as e:
        print(f"Error during teaser generation: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate teaser prompts: {e}")

@router.delete("/{character_id}", summary="Delete a character and all associated data")
async def delete_character(character_id: uuid.UUID, db=Depends(get_db)):
    """
    Deletes a character, all their associated data from the database, and all their files from the disk.
    """
    print(f"--- Attempting to delete character {character_id} ---")
    async with db.acquire() as connection:
        async with connection.transaction():
            # Check if character exists
            character = await connection.fetchrow("SELECT id FROM characters WHERE id = $1", character_id)
            if not character:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Character not found")

            # 1. Delete associated data from child tables
            await connection.execute("DELETE FROM character_llm_prompts WHERE character_id = $1", character_id)
            await connection.execute("DELETE FROM layers WHERE character_id = $1", character_id)
            await connection.execute("DELETE FROM content WHERE character_id = $1", character_id)
            await connection.execute("DELETE FROM reference_photos WHERE character_id = $1", character_id)

            # 2. Delete the character itself
            result = await connection.execute("DELETE FROM characters WHERE id = $1", character_id)
            
            if result == "DELETE 0":
                raise HTTPException(status_code=404, detail="Character not found during deletion process.")

    # 3. Delete character's upload directory
    try:
        character_dir = os.path.join(UPLOAD_DIRECTORY, str(character_id))
        if os.path.exists(character_dir):
            import shutil
            shutil.rmtree(character_dir)
            print(f"--- Successfully deleted directory: {character_dir} ---")
    except Exception as e:
        # Log the error but don't fail the request, as the DB part was successful
        print(f"!!! WARNING: Failed to delete directory for character {character_id}: {e} !!!")

    print(f"--- Successfully deleted character {character_id} and all associated data ---")
    return {"message": f"Character {character_id} deleted successfully"}
