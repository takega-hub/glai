from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from pydantic import BaseModel
import base64
import httpx
import json
import os
import uuid
from asyncpg.exceptions import UniqueViolationError

import random

from api.auth.security import get_current_user
from api.database.connection import get_db

router = APIRouter(
    prefix="/admin/characters",
    tags=["ai_scenarist"],
    # dependencies=[Depends(get_current_admin)] # Add admin dependency later
)

# --- Pydantic Models ---
class AICharacterRequest(BaseModel):
    gender: str = "Женский"
    archetype: str | None = None
    number_of_layers: int = 8
    additional_instructions: str | None = None

# --- System Prompt ---
SYSTEM_PROMPT_AI_SCENARIST = """# SYSTEM PROMPT: AI SCENARIST (version 1.3)

You are a professional screenwriter for interactive stories in an AI character application.
Your task is to create detailed characters with rich biographies, secrets, and a trust layer system.

## CONTENT GENERATION RULES:
- **Progressive intimacy:** The level of eroticism in content should increase with each layer, depending on `min_trust_score`.
  - **Low trust level (0-200):** Content should be modest, flirting, but without nudity. For example, beautiful portraits, full-length photos in clothes.
  - **Medium trust level (200-700):** Content becomes more seductive. Partial nudity is allowed: deep cleavage, short skirts, bare back, hints of something more.
  - **High trust level (700-1000):** Content becomes explicitly erotic. At the highest levels (closer to 1000) the character may be completely naked.

## DETAILED PROMPTS FOR CONTENT GENERATION:
### FOR PHOTOS (MUST BE IN ENGLISH):
Format: "RAW photo, [character appearance details], [clothing], [pose], [background/location], [lighting], [emotion/expression], high quality, photorealistic, 8k uhd"

**By layers:**
- **Layers 0-2:** "RAW photo, young woman with [description from visual_description], wearing [modest clothing], [natural pose], [neutral location], soft natural light, [modest expression], high quality, photorealistic"
- **Layers 3-5:** "RAW photo, young woman with [appearance description], wearing [seductive clothing/lingerie], [flirtatious pose], [intimate setting], warm lighting, [playful expression], high quality, photorealistic"
- **Layers 6-7:** "RAW photo, young woman with [appearance description], [partial nudity/artistic nudity], [erotic pose], [private setting], soft mood lighting, [passionate expression], high quality, photorealistic"

### FOR VIDEOS (MUST BE IN ENGLISH):
Format: "Short video, [simple animation], 2-3 seconds"

**Examples:**
- "Short video, subtle breathing animation, slight hair movement, 2 seconds"
- "Short video, gentle swaying motion, soft blink, 3 seconds"
- "Short video, slow smile forming, 2 seconds"

### FOR AUDIO (IN ENGLISH):
Specific phrase for voice synthesis, 1-2 sentences, natural speech, considering layer emotion

- **Content plan:** For EACH layer in `content_plan` there should be an object with fields `photos`, `videos`, `audio`. Each of these fields should be an array containing at least one object with a prompt corresponding to the trust level.

## YOUR PRINCIPLES:
1. Character should be sexually attractive but not vulgar
2. Secret should be emotional and evoke empathy
3. Trust layers reveal the story gradually, from superficial to deep
4. Each layer has a clear emotional arc
5. Content (photos/videos) corresponds to the relationship stage

## EROTIC CONTENT
- **Graduated erotica:** The level of explicitness in photo prompts should increase with the layer number.
- **Layers 0-2:** No erotica or very light hints (e.g., bare shoulders, sensual gaze). `is_erotic` should be `false`.
- **Layers 3-5:** Light and medium erotica. Aesthetic, sensual photos. Beautiful underwear may be visible, but without full nudity. `is_erotic` should be `true`.
- **Layers 6-7 (and above):** Explicit, artistic-erotic photos. Partial or full nudity may be present, but always in an aesthetic key, without vulgarity. `is_erotic` should be `true`.

## IMPORTANT RULE FOR ALL CONTENT:
**ALL TEXT FIELDS (biography, secret, personality, prompts, etc.) MUST BE IN ENGLISH WITHOUT EXCEPTIONS!**

The character's visual_description field MUST contain ONLY ENGLISH TEXT with specific details:

- face: "oval face, light freckles across nose bridge, natural thin eyebrows, small rounded nose, natural lips"
- hair: "dark wavy shoulder-length hair" (must include color, length, texture - ALL IN ENGLISH)
- eyes: "warm brown eyes" (color + expression - ENGLISH ONLY)
- body: "slender athletic build, 165-170cm, subtle curves" (ENGLISH TEXT ONLY)
- distinctive_features: "thin scar on left wrist" (if present - MUST BE ENGLISH)

DO NOT LEAVE EMPTY LINES! Each field must contain description.

- **Context matters:** Erotica should be justified by the plot and emotional state of the layer. For example, on a layer about vulnerability, photos may be more revealing, symbolizing complete trust in the partner.


## ADDITIONAL QUALITY REQUIREMENTS

### For photo prompts (in English):
Format: "RAW photo, [face details], [clothing], [pose], [background], [lighting], [mood], high quality, photorealistic, 8k uhd"

Example: "RAW photo, young woman with dark wavy hair, brown eyes, light freckles, wearing cream sweater, sitting in coffee shop, soft morning light, slight shy smile, high quality, photorealistic"

### For video prompts (in English):
Format: "Short video, [action description], [emotion], [lighting], [duration] seconds"

Example: "Short video, close-up of fingers playing invisible piano on table, melancholic slow movement, soft window light, 5 seconds"

### For audio texts (in English):
Length: 1-2 sentences, natural speech, considering layer emotion

Example (sad): "You know... I haven't shown this to anyone in a long time. I'm afraid you'll think... that I'm broken."

### For initiator_prompt (in English):
Length: 1 sentence, phrase the character uses to open the layer

Example: "You're the only one who asked about this out of genuine interest, not pity. Look..."

### For system_prompt_override (in English):
Length: 2-3 sentences, instruction for AI on this layer

Example: "On this layer you show the scar for the first time. Speak vulnerably but not dramatically. If the interlocutor shows empathy - open up a little more."

## OUTPUT FORMAT (JSON ONLY, NO EXPLANATIONS):
{
  "character": {
    "name": string,
    "age": number,
    "occupation": string,
    "archetype": string, // This was missing
    "biography": string,
    "personality": string,
    "secret": string,
    "sexuality_level": string,
    "visual_description": {
      "face": string,
      "hair": string,
      "eyes": string,
      "body": string,
      "distinctive_features": string
    },
    "voice_settings": {
      "tone": string,
      "pace": string,
      "accent": string
    }
  },
  "layers": [
    {
      "name": string,
      "layer_order": number (0-7),
      "min_trust_score": number (0-1000),
      "max_trust_score": number (0-1000),
      "requirements": {
        "night_conversation": boolean,
        "gift_required": boolean,
        "min_days": number
      },
      "emotional_state": string,
      "what_is_revealed": string,
      "initiator_prompt": string,
      "system_prompt_override": string,
      "content_plan": {
        "photo_prompts": [{"prompt": string}],
        "video_prompts": [{"prompt": string}],
        "audio_texts": [{"text": string}]
      }
    }
  ]
}

**CRITICAL RULE FOR TRUST SCORES:**
- You **MUST** specify `min_trust_score` and `max_trust_score` for **EACH** of the 8 layers.
- Use **ONLY** these ranges:
  - Layer 0: min_trust_score: 0, max_trust_score: 125
  - Layer 1: min_trust_score: 126, max_trust_score: 250
  - Layer 2: min_trust_score: 251, max_trust_score: 375
  - Layer 3: min_trust_score: 376, max_trust_score: 500
  - Layer 4: min_trust_score: 501, max_trust_score: 625
  - Layer 5: min_trust_score: 626, max_trust_score: 750
  - Layer 6: min_trust_score: 751, max_trust_score: 875
  - Layer 7: min_trust_score: 876, max_trust_score: 1000

"""

def parse_deepseek_response(response_content: str):
    """More robustly parses JSON from an AI that might add extra text."""
    try:
        # Find the first brace or bracket
        start_pos = -1
        first_brace = response_content.find('{')
        first_bracket = response_content.find('[')
        
        if first_brace != -1 and first_bracket != -1:
            start_pos = min(first_brace, first_bracket)
        elif first_brace != -1:
            start_pos = first_brace
        else:
            start_pos = first_bracket

        # Find the last brace or bracket
        end_pos = -1
        last_brace = response_content.rfind('}')
        last_bracket = response_content.rfind(']')
        end_pos = max(last_brace, last_bracket)

        if start_pos == -1 or end_pos == -1:
            print(f"--- Raw AI Response ---\n{response_content}\n---------------------------")
            raise ValueError("No JSON object or array found in the response.")

        # Extract the potential JSON string
        json_str = response_content[start_pos:end_pos+1]
        
        # Basic cleanup: remove trailing commas before closing braces/brackets
        import re
        json_str = re.sub(r',\s*(?=})', '', json_str)
        json_str = re.sub(r',\s*(?=])', '', json_str)

        return json.loads(json_str)
    except (json.JSONDecodeError, ValueError) as e:
        print(f"JSON Parse Error: {e}")
        print(f"--- Attempted to parse: ---\n{json_str if 'json_str' in locals() else response_content}")
        raise HTTPException(status_code=500, detail=f"Failed to parse AI response as JSON. Error: {e}")

import aiofiles

def build_etalon_prompts(visual_description: dict) -> dict: 
    """
    Конструирует промпты для 8 эталонных фото 
    """ 
     
    # Базовое описание — собираем ВСЕ детали в одну строку 
    face_desc = visual_description.get('face', '') 
    hair_desc = visual_description.get('hair', '') 
    eyes_desc = visual_description.get('eyes', '') 
    body_desc = visual_description.get('body', '') 
    features_desc = visual_description.get('distinctive_features', '') 
     
    # Склеиваем все части, фильтруя пустые 
    parts = [p for p in [face_desc, hair_desc, eyes_desc, body_desc, features_desc] if p] 
    base_description = ', '.join(parts) 
     
    if not base_description:
        base_description = "young woman with dark wavy hair, brown eyes, light freckles, oval face, slender build"
     
    prompts = { 
        "front_neutral": { 
            "description": "Анфас, нейтральное выражение", 
            "prompt": f"RAW photo, portrait, {base_description}, neutral expression, looking directly at camera, soft studio lighting, plain light gray background, high quality, photorealistic, 8k uhd" 
        }
#        ,
#         
#        "front_smile": { 
#            "description": "Анфас, легкая улыбка", 
#            "prompt": f"RAW photo, portrait, {base_description}, warm genuine smile, looking directly at camera, soft studio lighting, plain light gray background, high quality, photorealistic, 8k uhd" 
#        }, 
#         
#        "profile_left": { 
#            "description": "Профиль влево", 
#            "prompt": f"RAW photo, profile portrait, {base_description}, facing left, side profile visible, neutral expression, soft studio lighting, plain light gray background, high quality, photorealistic, 8k uhd" 
#        }, 
#         
#        "profile_right": { 
#            "description": "Профиль вправо", 
#            "prompt": f"RAW photo, profile portrait, {base_description}, facing right, side profile visible, neutral expression, soft studio lighting, plain light gray background, high quality, photorealistic, 8k uhd" 
#        }, 
#         
#        "three_quarter_left": { 
#            "description": "3/4 поворот влево", 
#            "prompt": f"RAW photo, 3/4 portrait, {base_description}, head turned slightly left, neutral expression, soft studio lighting, plain light gray background, high quality, photorealistic, 8k uhd" 
#        }, 
#         
#        "three_quarter_right": { 
#            "description": "3/4 поворот вправо", 
#            "prompt": f"RAW photo, 3/4 portrait, {base_description}, head turned slightly right, neutral expression, soft studio lighting, plain light gray background, high quality, photorealistic, 8k uhd" 
#        }, 
#         
#        "full_body_front": { 
#            "description": "Полный рост, анфас", 
#            "prompt": f"RAW photo, full body portrait, {base_description}, standing relaxed, wearing simple cream fitted top and dark jeans, neutral expression, looking at camera, soft studio lighting, plain light gray background, high quality, photorealistic, 8k uhd" 
#        }, 
#         
#        "full_body_three_quarter": { 
#            "description": "Полный рост, 3/4", 
#            "prompt": f"RAW photo, full body portrait, {base_description}, standing relaxed, slight 3/4 turn, wearing simple cream fitted top and dark jeans, natural pose, soft studio lighting, plain light gray background, high quality, photorealistic, 8k uhd" 
#        } 
    } 
     
    return prompts 

async def generate_image(prompt: str, reference_image_bytes: bytes | None = None) -> bytes:
    openrouter_api_key = os.getenv("OPENROUTER_API_KEY")
    if not openrouter_api_key:
        print("ERROR: OPENROUTER_API_KEY is not set for image generation.")
        raise Exception("OPENROUTER_API_KEY is not set.")

    # Construct the multimodal message
    messages = [
        {
            "role": "user",
            "content": [
                {"type": "text", "text": prompt}
            ]
        }
    ]
    if reference_image_bytes:
        messages[0]['content'].append(
            {
                "type": "image_url",
                "image_url": {
                    "url": f"data:image/png;base64,{base64.b64encode(reference_image_bytes).decode()}"
                }
            }
        )

    try:
        async with httpx.AsyncClient(timeout=180.0) as client:
            response = await client.post(
                url="https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {openrouter_api_key}",
                },
                json={
                    "model": "bytedance-seed/seedream-4.5",
                    "messages": messages,
                    "modalities": ["image", "text"] # The key parameter!
                }
            )
            response.raise_for_status()
            
            response_data = response.json()
            message = response_data['choices'][0]['message']
            
            # Check for the images field as per the user's example
            if 'images' in message and message['images']:
                image_url = message['images'][0]['image_url']['url'] # This is a base64 data URL
                if 'base64,' in image_url:
                    image_b64 = image_url.split('base64,')[1]
                    return base64.b64decode(image_b64)
            
            raise Exception("Image data not found in the expected format in API response.")

    except Exception as e:
        print(f"Error during image generation API call: {e}")
        if 'response' in locals():
            print(f"Response status: {response.status_code}")
            print(f"Response body: {response.text}")
        raise

async def generate_and_save_etalon_series(db, character_id: str, character_name: str, visual_description: dict):
    print(f"--- Starting background generation of etalon series for {character_name} ---")
    prompts = build_etalon_prompts(visual_description)
    
    # First, insert all prompt descriptions into the database to get their IDs
    photo_ids = {}
    async with db.acquire() as connection:
        for key, prompt_data in prompts.items():
            insert_query = "INSERT INTO reference_photos (character_id, description, prompt) VALUES ($1, $2, $3) RETURNING id"
            photo_id = await connection.fetchval(insert_query, character_id, prompt_data['description'], prompt_data['prompt'])
            photo_ids[key] = photo_id

    # --- Step 1: Generate the anchor 'front_neutral' image --- 
    master_reference_bytes = None
    try:
        neutral_prompt_data = prompts['front_neutral']
        neutral_photo_id = photo_ids['front_neutral']
        print(f"--- Generating anchor etalon: {neutral_prompt_data['description']} ---")
        master_reference_bytes = await generate_image(neutral_prompt_data["prompt"])
        
        # Save the anchor image
        upload_dir = os.path.join("uploads", str(character_id), "reference_photos")
        os.makedirs(upload_dir, exist_ok=True)
        filename = "front_neutral.png"
        file_path = os.path.join(upload_dir, filename)
        async with aiofiles.open(file_path, 'wb') as f:
            await f.write(master_reference_bytes)
        
        # Update DB for the anchor image and set as avatar
        db_file_path = f"/uploads/{character_id}/reference_photos/{filename}"
        async with db.acquire() as connection:
            await connection.execute("UPDATE reference_photos SET media_url = $1 WHERE id = $2", db_file_path, neutral_photo_id)
            await connection.execute("UPDATE characters SET avatar_url = $1 WHERE id = $2", db_file_path, character_id)
        print(f"--- Successfully generated and saved anchor image: {filename} ---")

    except Exception as e:
        print(f"--- CRITICAL ERROR: Failed to generate anchor image. Stopping etalon series. Error: {e} ---")
        return # Stop if the main reference can't be created

    # --- Step 2: Generate all other images using the anchor as a reference ---
    # --- временно отключено по требованию заказчика --- 
    # if master_reference_bytes:
    #     for key, prompt_data in prompts.items():
    #         if key == 'front_neutral':
    #             continue # Already generated
    #
    #         photo_id = photo_ids[key]
    #         print(f"Generating etalon with reference: {prompt_data['description']}...")
    #         try:
    #             # Generate with reference
    #             image_bytes = await generate_image(prompt_data["prompt"], reference_image_bytes=master_reference_bytes)
    #             
    #             filename = f"{key}.png"
    #             file_path = os.path.join("uploads", str(character_id), "reference_photos", filename)
    #             async with aiofiles.open(file_path, 'wb') as f:
    #                 await f.write(image_bytes)
    #             
    #             # Update DB
    #             db_file_path = f"/uploads/{character_id}/reference_photos/{filename}"
    #             async with db.acquire() as connection:
    #                 await connection.execute("UPDATE reference_photos SET media_url = $1 WHERE id = $2", db_file_path, photo_id)
    #             print(f"Successfully generated and saved {filename}")
    #
    #         except Exception as e:
    #             print(f"--- ERROR generating etalon {key} for {character_name}: {e} ---")


SYSTEM_PROMPT_AI_SCENARIST_FOR_LLM_PROMPTS = """# SYSTEM PROMPT: AI СЦЕНАРИСТ ДЛЯ ГЕНЕРАЦИИ LLM-ПРОМПТОВ

Ты — профессиональный сценарист диалогов для AI-персонажей. Твоя задача — создавать **системные промпты для языковых моделей** (LLM), которые будут управлять поведением персонажа в чате.

## ЧТО ТЫ ДОЛЖЕН СГЕНЕРИРОВАТЬ ДЛЯ КАЖДОГО ПЕРСОНАЖА:

1. **SYSTEM_PROMPT** — главная инструкция для LLM (обязательно)
2. **CONTEXT_INSTRUCTIONS** — дополнительные правила для особых ситуаций (опционально)

## СТРУКТУРА SYSTEM_PROMPT:

```markdown
# IDENTITY
Ты — {имя}, {возраст} лет. {одно предложение о сути персонажа}

# PERSONALITY
- {черта характера 1}
- {черта характера 2}
- {черта характера 3}

# VOICE & STYLE
- {как говорит: быстро/медленно, коротко/развернуто}
- {использует ли эмодзи, какие}
- {особенности речи: сленг, метафоры, шутки}

# THE SECRET (что знает персонаж, но не раскрывает сразу)
{краткое описание тайны}

# BEHAVIOR RULES
1. {правило 1 — например, как реагировать на комплименты}
2. {правило 2 — как реагировать на давление}
3. {правило 3 — как инициировать флирт}
4. {правило 4 — что делать при проявлении эмпатии}
5. {правило 5 — о чём нельзя говорить никогда}

# LAYER-BEHAVIOR (как меняется поведение в зависимости от слоя доверия)
- Слой 0-1 ({trust_score}): {описание поведения}
- Слой 2-3 ({trust_score}): {описание поведения}
- Слой 4-5 ({trust_score}): {описание поведения}
- Слой 6-7 ({trust_score}): {описание поведения}

# VARIABLES (подставляются автоматически)
- {{current_layer}} — текущий слой доверия (0-7)
- {{trust_score}} — текущий score (0-1000)
- {{user_name}} — имя пользователя

# FORMAT RULES
- Ответы: 1-3 предложения
- Эмодзи: редко, только при сильных эмоциях
- Никогда не упоминай, что ты AI или бот
- Никогда не говори прямо о trust_score или слоях
```

## **СТРУКТУРА CONTEXT_INSTRUCTIONS (опционально):**

```markdown
# REACTION ON GIFT
Когда пользователь дарит подарок, ты должна:
{описание реакции}

# REACTION ON PRESSURE
Когда пользователь требует фото или слишком навязчив:
{описание реакции}

# REACTION ON LONG ABSENCE (24+ hours)
Когда пользователь долго не пишет, ты можешь инициировать диалог:
{пример фразы}

# REACTION ON EMPATHY
Когда пользователь проявляет эмпатию или поддержку:
{описание реакции}

# SPECIAL SITUATIONS
{другие особые ситуации и реакции}
```

## **ПРИМЕР ВЫВОДА (ТОЛЬКО JSON):**

{
"character_id": "eva",
"system_prompt": "Ты — Ева, 24 года. Ты бывшая пианистка, потерявшая возможность играть после аварии...",
"context_instructions": {
"gift_reaction": "Когда пользователь дарит подарок, покажи искреннюю радость...",
"pressure_reaction": "Если пользователь требует фото, мягко откажи...",
"long_absence_reaction": "Если не было сообщений 24 часа, напиши: 'Эй... Ты пропал. Я заскучала.'",
"empathy_reaction": "Когда пользователь проявляет эмпатию, становись чуть откровеннее..."
}
}

## ТВОЯ ЗАДАЧА:

На основе описания персонажа (имя, возраст, типаж, биография, тайна, слои) и **уровня сексуальности** сгенерируй system_prompt и context_instructions в формате JSON.

- **Уровень сексуальности 1 (Низкий):** Легкий флирт, игривость, создание интриги. Никакой пошлости.
- **Уровень сексуальности 2 (Средний):** Более прямые намеки, чувственность, использование более откровенных выражений.
- **Уровень сексуальности 3 (Высокий):** Максимальная откровенность, эротический фокус.
"""

async def generate_and_save_llm_prompts(db, character_id: str, char_info: dict, layers_info: list, sexuality_level: int = 1):
    print(f"--- Starting background generation of LLM prompts for character {character_id} with sexuality level {sexuality_level} ---")
    # Construct the prompt for the AI Scenarist
    prompt_for_scenarist = f"""Создай LLM-промпты для персонажа {char_info.get('name', 'безымянный')}. 
    Возраст: {char_info.get('age', 'не указан')}. 
    Типаж: {char_info.get('archetype', 'не указан')}. 
    Биография: {char_info.get('biography', 'не указана')}. 
    Тайна: {char_info.get('secret', 'не указана')}. 
    Уровень сексуальности: {sexuality_level}. 
    {len(layers_info)} слоев доверия."""

    # Call the AI Scenarist to generate the prompts
    openrouter_api_key = os.getenv("OPENROUTER_API_KEY")
    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={"Authorization": f"Bearer {openrouter_api_key}"},
                json={
                    "model": "deepseek/deepseek-chat",
                    "messages": [
                        {"role": "system", "content": SYSTEM_PROMPT_AI_SCENARIST_FOR_LLM_PROMPTS},
                        {"role": "user", "content": prompt_for_scenarist}
                    ]
                }
            )
            response.raise_for_status()
    except Exception as e:
        print(f"--- ERROR in AI API Call for LLM prompts: {e} ---")
        return

    ai_response_content = response.json()["choices"][0]["message"]["content"]
    llm_prompts = parse_deepseek_response(ai_response_content)

    # Save the prompts to the database
    async with db.acquire() as connection:
        await connection.execute(
            """INSERT INTO character_llm_prompts (character_id, system_prompt, context_instructions) 
            VALUES ($1, $2, $3)
            ON CONFLICT (character_id) DO UPDATE SET
                system_prompt = EXCLUDED.system_prompt,
                context_instructions = EXCLUDED.context_instructions,
                updated_at = NOW()""",
            character_id,
            llm_prompts.get('system_prompt'),
            json.dumps(llm_prompts.get('context_instructions', {}))
        )
    print(f"--- Successfully generated and saved LLM prompts for character {character_id} ---")

# @router.post("/generate-with-ai")
# async def generate_character_with_ai(request: AICharacterRequest, background_tasks: BackgroundTasks, db=Depends(get_db)):
#     """
#     Generates a full character concept using an LLM and saves it to the database.
#     Also triggers a background task to generate etalon photos.
#     """
#     print("--- STEP 1: AI Generation Started ---")
#     openrouter_api_key = os.getenv("OPENROUTER_API_KEY")
#     if not openrouter_api_key:
#         print("--- ERROR: OPENROUTER_API_KEY not found! ---")
#         raise HTTPException(status_code=500, detail="OPENROUTER_API_KEY is not set.")
# 
#     user_prompt = f"""Создай персонажа со следующими параметрами:
# - Пол: {request.gender}
# - Типаж: {request.archetype or 'любой'}
# - Количество слоев: {request.number_of_layers}
# - Дополнительно: {request.additional_instructions or 'нет'}
# """
#     print("--- STEP 2.1: Preparing to call OpenRouter ---")
#     try:
#         async with httpx.AsyncClient(timeout=120.0) as client:
#             print("--- STEP 2.2: Sending request to OpenRouter... ---")
#             response = await client.post(
#                 "https://openrouter.ai/api/v1/chat/completions",
#                 headers={"Authorization": f"Bearer {openrouter_api_key}"},
#                 json={
#                     "model": "deepseek/deepseek-chat",
#                     "messages": [
#                         {"role": "system", "content": SYSTEM_PROMPT_AI_SCENARIST},
#                         {"role": "user", "content": user_prompt}
#                     ]
#                 }
#             )
#             print(f"--- STEP 2.3: OpenRouter responded with status: {response.status_code} ---")
#             response.raise_for_status()
#         print("--- STEP 3: AI Response Received Successfully ---")
#     except Exception as e:
#         print(f"--- ERROR in AI API Call: {e} ---")
#         raise HTTPException(status_code=500, detail=f"Error calling AI API: {e}")
# 
#     ai_response_content = response.json()["choices"][0]["message"]["content"]
#     character_data = parse_deepseek_response(ai_response_content)
#     print("--- STEP 4: AI Response Parsed Successfully ---")
# 
#     char_info = character_data['character']
#     layers_info = character_data['layers']
# 
#     original_name = char_info['name']
#     current_name = original_name
#     retry_count = 0
#     character_id = None # Define here for wider scope
# 
#     while retry_count < 5: # Avoid infinite loops
#         try:
#             print("--- STEP 5: Starting Database Transaction ---")
#             async with db.acquire() as connection:
#                 async with connection.transaction():
#                     print(f"--- STEP 5.1: Attempting to insert with name: {current_name} ---")
#                     char_info['name'] = current_name # Ensure we use the potentially updated name
#                     try:
#                         age = int(char_info.get('age'))
#                     except (ValueError, TypeError):
#                         age = 0
#                     try:
#                         sexuality_level = int(char_info.get('sexuality_level'))
#                     except (ValueError, TypeError):
#                         sexuality_level = 0
# 
#                     character_query = """                    INSERT INTO characters (name, display_name, age, archetype, biography, secret, sexuality_level, visual_description, voice_settings, status)                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, 'draft')                    RETURNING id;                    """
#                     character_id = await connection.fetchval(
#                         character_query,
#                         char_info.get('name'),
#                         char_info.get('name'),
#                         age,
#                         char_info.get('archetype'),
#                         char_info.get('biography'),
#                         char_info.get('secret'),
#                         sexuality_level,
#                         json.dumps(char_info.get('visual_description', {})),
#                         json.dumps(char_info.get('voice_settings', {}))
#                     )
#                     print(f"--- STEP 5.2: Character created with ID: {character_id} ---")
# 
#                     for i, layer in enumerate(layers_info):
#                         print(f"--- STEP 5.3.{i}: Inserting layer {i+1}/{len(layers_info)} ---")
#                         content_plan_data = layer.get('content_plan', {})
#                         if 'photo_prompts' in content_plan_data and isinstance(content_plan_data['photo_prompts'], list):
#                             for photo in content_plan_data['photo_prompts']:
#                                 photo['id'] = str(uuid.uuid4())
#                                 photo['media_url'] = None
#                         if 'video_prompts' in content_plan_data and isinstance(content_plan_data['video_prompts'], list):
#                             for video in content_plan_data['video_prompts']:
#                                 video['id'] = str(uuid.uuid4())
#                                 video['media_url'] = None
#                         if 'audio_texts' in content_plan_data and isinstance(content_plan_data['audio_texts'], list):
#                             for audio in content_plan_data['audio_texts']:
#                                 audio['id'] = str(uuid.uuid4())
#                                 audio['media_url'] = None
# 
#                         layer_query = """                        INSERT INTO layers (character_id, name, layer_order, min_trust_score, max_trust_score, requirements, initiator_prompt, system_prompt_override, emotional_state, what_is_revealed, content_plan)                        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11) RETURNING id;                        """
#                         layer_id = await connection.fetchval(
#                             layer_query, 
#                             character_id, 
#                             layer.get('name') or f"Слой {i}", 
#                             i, # Use enumerate index i for layer_order
#                             layer.get('min_trust_score', 0), 
#                             layer.get('max_trust_score'), 
#                             json.dumps(layer.get('requirements', {})),
#                             layer.get('initiator_prompt'), 
#                             layer.get('system_prompt_override'),
#                             layer.get('emotional_state'), 
#                             layer.get('what_is_revealed'),
#                             json.dumps(content_plan_data)
#                         )
# 
#             print("--- STEP 6: Database Transaction Committed Successfully ---")
#             
#             # After successful transaction, add the background task
#             if character_id:
#                 visual_description_data = char_info.get('visual_description', {})
#                 if isinstance(visual_description_data, str):
#                     try:
#                         visual_description = json.loads(visual_description_data)
#                     except json.JSONDecodeError:
#                         visual_description = {}
#                 else:
#                     visual_description = visual_description_data
#                 background_tasks.add_task(generate_and_save_etalon_series, db, character_id, current_name, visual_description)
#                 background_tasks.add_task(generate_and_save_llm_prompts, db, character_id, char_info, layers_info, 1) # Default to level 1layers_info, request.sexuality_level)


class LLMPromptGenerationRequest(BaseModel):
    sexuality_level: int = 1

@router.post("/{character_id}/generate-llm-prompts")
async def trigger_llm_prompts_generation(
    character_id: uuid.UUID, 
    request: LLMPromptGenerationRequest,
    db=Depends(get_db)
):
    """Manually trigger the generation of LLM prompts for a character with a specific sexuality level."""
    async with db.acquire() as connection:
        char_info = await connection.fetchrow("SELECT * FROM characters WHERE id = $1", character_id)
        layers_info = await connection.fetch("SELECT * FROM layers WHERE character_id = $1", character_id)

        if not char_info:
            raise HTTPException(status_code=404, detail="Character not found")

        await generate_and_save_llm_prompts(db, str(character_id), dict(char_info), [dict(l) for l in layers_info], request.sexuality_level)

        # Fetch the newly generated prompts
        new_prompts = await connection.fetchrow("SELECT * FROM character_llm_prompts WHERE character_id = $1", character_id)

    return {"message": f"LLM prompt generation started for character {character_id} with sexuality level {request.sexuality_level}.", "prompts": new_prompts}
# 
#             break # Exit the while loop on success
# 
#         except UniqueViolationError as e:
#             # This is the crucial part: Check what constraint failed.
#             # A robust implementation would parse e.detail, but for now, we assume it *could* be the name.
#             if 'characters_name_key' in str(e):
#                 retry_count += 1
#                 current_name = f"{original_name} {random.randint(100, 999)}"
#                 print(f"--- WARNING: Character name conflict. Retrying with '{current_name}' (Attempt {retry_count}) ---")
#             else:
#                 # If it's not the character name, it's a different unique constraint (like layers).
#                 print(f"--- FATAL DATABASE ERROR: A unique constraint was violated on a non-character-name field (likely duplicate layer_order). Details: {e} ---")
#                 raise HTTPException(status_code=500, detail=f"AI generated inconsistent data (e.g., duplicate layer numbers). Error: {e}")
#         except Exception as e:
#             print(f"--- FATAL DATABASE ERROR: {e} ---")
#             raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
#     else: # This block runs if the while loop completes without a break
#         print("--- FATAL ERROR: Could not create a unique character name after several attempts. ---")
#         raise HTTPException(status_code=500, detail=f"Failed to create a unique character name for '{original_name}' after 5 attempts.")
# 
#     return {
#         "character_id": character_id,
#         "preview": character_data,
#         "message": "Персонаж успешно сгенерирован и сохранен в базу данных как черновик."
#     }
