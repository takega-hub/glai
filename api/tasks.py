from typing import Optional, Dict
import os
import uuid
import json
import aiofiles

from api.services.comfy_service import ComfyService
from api.services.ai_dialogue_v2 import AIDialogueEngine
from api.services.image_generator import OpenRouterImageGenerator


# --- Helper Function (used by unlock_and_generate_photo_task) ---
async def _unlock_photo_in_db(db, photo_id: uuid.UUID, character_id: uuid.UUID, user_id: uuid.UUID):
    """Marks a photo as unlocked in the database within a background task."""
    print(f"--- [BG Task] Unlocking photo {photo_id} for character {character_id} user {user_id} ---")
    async with db.acquire() as connection:
        async with connection.transaction():
            # First, try to unlock in content table (for teaser photos)
            updated_teaser = await connection.execute(
                "UPDATE content SET is_locked = FALSE WHERE id = $1 AND subtype = 'teaser' RETURNING id",
                photo_id
            )
            
            # If it was a teaser photo, also insert into user_unlocked_content
            if updated_teaser and updated_teaser != "UPDATE 0":
                await connection.execute(
                    """INSERT INTO user_unlocked_content (user_id, character_id, content_id) 
                       VALUES ($1, $2, $3) ON CONFLICT (user_id, character_id, content_id) DO NOTHING""",
                    user_id, character_id, photo_id
                )
                print(f"--- [BG Task] Unlocked teaser photo {photo_id} and added to user_unlocked_content ---")
                return
            
            # If not a teaser, try to unlock in layers content_plan
            all_layers = await connection.fetch("SELECT id, content_plan FROM layers WHERE character_id = $1", character_id)
            for layer in all_layers:
                if not layer['content_plan']: continue
                content_plan = json.loads(layer['content_plan'])
                found_and_updated = False
                if 'photo_prompts' in content_plan:
                    for item in content_plan['photo_prompts']:
                        if item.get('id') == str(photo_id):
                            item['is_locked'] = False
                            found_and_updated = True
                            break
                if found_and_updated:
                    await connection.execute(
                        "UPDATE layers SET content_plan = $1 WHERE id = $2",
                        json.dumps(content_plan), layer['id']
                    )
                    # Also insert into user_unlocked_content for layer photos
                    await connection.execute(
                        """INSERT INTO user_unlocked_content (user_id, character_id, content_id) 
                           VALUES ($1, $2, $3) ON CONFLICT (user_id, character_id, content_id) DO NOTHING""",
                        user_id, character_id, photo_id
                    )
                    print(f"--- [BG Task] Unlocked layer photo {photo_id} and added to user_unlocked_content ---")
                    return

# --- Background Tasks ---

async def generate_intimate_photo_task(db, character_id: uuid.UUID, user_id: uuid.UUID, intimacy_analysis: Dict):
    """Background task for generating special intimate photos after a large gift."""
    print(f"--- Starting intimate photo generation for user {user_id} ---")
    try:
        dialogue_engine = AIDialogueEngine(db)
        comfy_service = ComfyService()
        
        async with db.acquire() as connection:
            character = await connection.fetchrow("SELECT * FROM characters WHERE id = $1", character_id)
            if not character:
                print(f"Character {character_id} not found.")
                return

            # Get the base visual description of the character
            base_description_text = ""
            if character.get('visual_description'):
                try:
                    desc_data = json.loads(character['visual_description'])
                    base_description_text = ", ".join(f"{k.replace('_', ' ')} is {v}" for k, v in desc_data.items())
                except (json.JSONDecodeError, TypeError):
                    if isinstance(character['visual_description'], str):
                        base_description_text = character['visual_description']

            # Generate a powerful, context-aware supplemental prompt from the user's request
            supplemental_prompt_details = await dialogue_engine.generate_on_demand_image_prompt(
                user_request=intimacy_analysis.get("user_intent", "a special photo"),
                character_data=dict(character),
                trust_score=100, # Assume high trust for this task
                style="cinematic, photorealistic",
                conversation_history=[] # No history needed for this task
            )
            
            if not supplemental_prompt_details or not supplemental_prompt_details.get("prompt"):
                print("Failed to generate supplemental image prompt.")
                return

            supplemental_prompt = supplemental_prompt_details["prompt"]

            # Combine the base description with the supplemental prompt
            final_prompt = f"{base_description_text}, {supplemental_prompt}"
            print(f"--- Constructed Final Prompt: {final_prompt} ---")
            
            # Get face image
            face_image_path = character['avatar_url'].lstrip('/')
            if not os.path.exists(face_image_path):
                print(f"Reference face image not found at path: {face_image_path}")
                return

            with open(face_image_path, "rb") as f:
                face_image_bytes = f.read()
            
            # Generate image
            generated_image_bytes = await comfy_service.generate_image_with_face(
                text_prompt=final_prompt, 
                face_image_bytes=face_image_bytes
            )

            if not generated_image_bytes:
                print("Intimate image generation failed.")
                return

            # Save and send image
            upload_dir = f"uploads/{character_id}/generated"
            os.makedirs(upload_dir, exist_ok=True)
            file_path = os.path.join(upload_dir, f"{uuid.uuid4()}.png")
            
            async with aiofiles.open(file_path, 'wb') as out_file:
                await out_file.write(generated_image_bytes)
            
            image_url = f"/{file_path}"
            
            # Send a notification to the user with the photo
            notification_message = "Я долго готовилась и сделала это фото специально для тебя... Надеюсь, оно тебе понравится. 😘"
            await connection.execute(
                "INSERT INTO notifications (user_id, character_id, message, image_url) VALUES ($1, $2, $3, $4)",
                user_id, character_id, notification_message, image_url
            )
            
            print(f"--- Successfully generated and sent notification for intimate photo to user {user_id} ---")

    except Exception as e:
        print(f"!!! ERROR in intimate photo generation task: {e} !!!")

async def generate_and_send_photo_task(db, character_id: uuid.UUID, user_id: uuid.UUID, user_prompt: str):
    """Background task for on-demand photo generation (Plan C)."""
    print(f"--- Starting on-demand photo generation for user {user_id} with prompt: {user_prompt} ---")
    comfy_service = ComfyService()
    dialogue_engine = AIDialogueEngine(db)
    try:
        async with db.acquire() as connection:
            character = await connection.fetchrow("SELECT avatar_url, visual_description FROM characters WHERE id = $1", character_id)
            if not character or not character['avatar_url']:
                print(f"Character {character_id} or avatar_url not found.")
                return

            base_description_json = character['visual_description']
            base_description_text = ""
            if base_description_json:
                try:
                    desc_data = json.loads(base_description_json)
                    base_description_text = ", ".join(f"{k.replace('_', ' ')} is {v}" for k, v in desc_data.items())
                except (json.JSONDecodeError, TypeError):
                    if isinstance(base_description_json, str): base_description_text = base_description_json

            face_image_path = character['avatar_url'].lstrip('/')
            if not os.path.exists(face_image_path): 
                print(f"Reference face image not found at path: {face_image_path}")
                return

            with open(face_image_path, "rb") as f:
                face_image_bytes = f.read()

        enhanced_english_prompt = await dialogue_engine.enhance_image_prompt(user_prompt)
        final_prompt = f"{base_description_text}, {enhanced_english_prompt}"

        generated_image_bytes = await comfy_service.generate_image_with_face(text_prompt=final_prompt, face_image_bytes=face_image_bytes)

        if not generated_image_bytes: 
            print("On-demand image generation failed.")
            return

        upload_dir = "uploads/generated_photos"
        os.makedirs(upload_dir, exist_ok=True)
        file_path = os.path.join(upload_dir, f"{uuid.uuid4()}.jpg")
        
        async with aiofiles.open(file_path, 'wb') as out_file:
            await out_file.write(generated_image_bytes)
        
        image_url = f"/{file_path}"

        async with db.acquire() as connection:
            response_text = "Я сделала это фото специально для тебя, по твоей просьбе. Как тебе?"
            await connection.execute(
                "INSERT INTO messages (character_id, user_id, response, image_url, created_at) VALUES ($1, $2, $3, $4, NOW())",
                character_id, user_id, response_text, image_url
            )
        
        print(f"--- Successfully generated and sent on-demand photo to user {user_id} ---")

    except Exception as e:
        print(f"!!! ERROR in on-demand photo generation task: {e} !!!")

async def unlock_and_generate_photo_task(db, character_id: uuid.UUID, user_id: uuid.UUID, photo_id: uuid.UUID, prompt: str, source: str, layer_id: Optional[int] = None):
    """Background task to generate an image for a locked prompt, update the database, and send it (Plan B)."""
    print(f"--- Starting photo unlock/generation task for photo {photo_id} ---")
    try:
        comfy_service = ComfyService()

        async with db.acquire() as connection:
            character = await connection.fetchrow("SELECT avatar_url, visual_description FROM characters WHERE id = $1", character_id)
            if not character or not character['avatar_url']: 
                print(f"Character {character_id} or avatar_url not found.")
                return

            face_image_path = character['avatar_url'].lstrip('/')
            if not os.path.exists(face_image_path): 
                print(f"Reference face image not found at path: {face_image_path}")
                return

            with open(face_image_path, "rb") as f:
                face_image_bytes = f.read()

            base_description_json = character['visual_description']
            base_description_text = ""
            if base_description_json:
                try:
                    desc_data = json.loads(base_description_json)
                    base_description_text = ", ".join(f"{k.replace('_', ' ')} is {v}" for k, v in desc_data.items())
                except (json.JSONDecodeError, TypeError):
                    if isinstance(base_description_json, str): base_description_text = base_description_json

        final_prompt = f"{base_description_text}, {prompt}"
        image_bytes = await comfy_service.generate_image_with_face(text_prompt=final_prompt, face_image_bytes=face_image_bytes)

        if not image_bytes: 
            print(f"!!! Image generation failed for prompt: {prompt} !!!")
            return

        upload_dir = f"uploads/{character_id}/content"
        os.makedirs(upload_dir, exist_ok=True)
        file_path = os.path.join(upload_dir, f"{photo_id}.png")
        async with aiofiles.open(file_path, 'wb') as f:
            await f.write(image_bytes)
        
        media_url = f"/{file_path}"
        print(f"--- Saved generated photo to {media_url} ---")

        await _unlock_photo_in_db(db, photo_id, character_id, user_id)

        async with db.acquire() as connection:
            response_text = "Вот, как и обещала, небольшой сюрприз для тебя. 💕"
            await connection.execute(
                "INSERT INTO messages (character_id, user_id, response, image_url, created_at) VALUES ($1, $2, $3, $4, NOW())",
                character_id, user_id, response_text, media_url
            )

        print(f"--- Successfully generated, unlocked, and sent photo {photo_id} to user {user_id} ---")

    except Exception as e:
        print(f"!!! ERROR in unlock_and_generate_photo_task: {e} !!!")
