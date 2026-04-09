import uuid
import json

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from typing import Dict, Any, Optional, List, Tuple

from api.auth.security import get_current_user
from api.database.connection import get_db
from api.services.ai_dialogue_v2 import AIDialogueEngine
from api.services.comfy_service import ComfyService
from api.tasks import generate_intimate_photo_task

from pydantic import BaseModel
from enum import Enum
from datetime import datetime

# --- Local Pydantic Models ---
class GiftType(str, Enum):
    small = "small"
    medium = "medium"
    large = "large"

class MessageRequest(BaseModel):
    character_id: uuid.UUID
    message: str

class MessageResponse(BaseModel):
    response: str
    response_parts: List[str]
    image_url: Optional[str] = None

class GiftRequest(BaseModel):
    character_id: uuid.UUID
    gift_type: GiftType
    intimacy_analysis: Optional[Dict] = None

class GiftResponse(BaseModel):
    new_trust_score: int
    new_token_balance: int
    message: str
    character_response: str
    character_response_parts: List[str] = []
    unlocked_photo_url: Optional[str] = None

class HistoryMessage(BaseModel):
    role: str
    content: str
    image_url: Optional[str] = None
    created_at: str

class CharacterInfo(BaseModel):
    id: uuid.UUID
    name: str
    display_name: str
    personality_type: Optional[str] = None

class HistoryResponse(BaseModel):
    messages: List[HistoryMessage]
    trust_score: int
    current_layer: int
    character_info: CharacterInfo

router = APIRouter()

async def _unlock_photo(db, user_id: uuid.UUID, photo_id: uuid.UUID, character_id: uuid.UUID):
    """Synchronously marks a photo as unlocked in the database."""
    print(f"--- [Immediate] Unlocking photo {photo_id} for character {character_id} ---")
    async with db.acquire() as connection:
        async with connection.transaction():
            # Also record this unlock in the user-specific gallery table
            await connection.execute(
                """INSERT INTO user_unlocked_content (user_id, character_id, content_id)
                   VALUES ($1, $2, $3)
                   ON CONFLICT (user_id, character_id, content_id) DO NOTHING""",
                user_id, character_id, photo_id
            )

            updated_teaser = await connection.execute(
                "UPDATE content SET is_locked = FALSE WHERE id = $1 AND subtype = 'teaser' RETURNING id",
                photo_id
            )
            if not updated_teaser or updated_teaser == "UPDATE 0":
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
                        print(f"--- [Immediate] Unlocked photo {photo_id} within layer {layer['id']} ---")
                        return

@router.post("/dialogue/send-message", response_model=MessageResponse)
async def send_message(
    request: MessageRequest,
    current_user=Depends(get_current_user),
    db=Depends(get_db),
    dialogue_engine: AIDialogueEngine = Depends(lambda db=Depends(get_db): AIDialogueEngine(db))
):
    async with db.acquire() as connection:
        character = await connection.fetchrow(
            "SELECT id, name, display_name, textual_description, visual_description, avatar_url, personality_type, llm_model FROM characters WHERE id = $1",
            request.character_id
        )
        user_state = await connection.fetchrow(
            "SELECT trust_score, conversation_history, current_layer FROM user_character_state WHERE user_id = $1 AND character_id = $2",
            current_user["user_id"], request.character_id
        )
        if not character or not user_state: raise HTTPException(status_code=404, detail="Character or user state not found")

        conversation_history = json.loads(user_state["conversation_history"] or "[]")

        character_layers = await connection.fetch("SELECT * FROM layers WHERE character_id = $1 ORDER BY layer_order ASC", request.character_id)

        response_data = await dialogue_engine.generate_character_response(
            character_data=dict(character), 
            user_message=request.message,
            conversation_history=conversation_history, 
            user_trust_score=user_state["trust_score"], 
            current_layer=user_state["current_layer"], 
            character_layers=character_layers, 
            db_connection=connection,
            user_name=current_user["user_name"]
        )

        print(f"[DEBUG] Response from Dialogue Engine: {response_data}")

        # Combine all parts of the response
        all_parts = [response_data["response"]] + response_data.get("message_parts", [])
        image_url_first_part = response_data.get("image_url")

        # 3. Update history and save each part as a separate message
        for i, part in enumerate(all_parts):
            if not part or not part.strip():
                continue

            # Add to conversation history for the state table
            conversation_history.append({"role": "assistant", "content": part})

            # Insert into messages table
            current_image_url = image_url_first_part if i == 0 else None
            await connection.execute(
                "INSERT INTO messages (character_id, user_id, message, response, image_url, created_at) VALUES ($1, $2, $3, $4, $5, NOW())",
                request.character_id,
                current_user["user_id"],
                request.message if i == 0 else None,  # Associate user message only with the first part
                part,
                current_image_url
            )

        # 4. Save the fully updated history once
        await connection.execute(
            "UPDATE user_character_state SET conversation_history = $1 WHERE user_id = $2 AND character_id = $3",
            json.dumps(conversation_history), current_user["user_id"], request.character_id
        )
        
        # 5. Decrement tokens (only once per user message)
        await connection.execute("UPDATE users SET tokens = tokens - 1 WHERE id = $1", current_user["user_id"])

    # The client will handle the animation based on the original full response
    return MessageResponse(response=response_data["response"], response_parts=response_data["message_parts"], image_url=image_url_first_part)

GIFT_CONFIG = {
    "small": {"trust_gain": 10, "token_cost": 10},
    "medium": {"trust_gain": 30, "token_cost": 25},
    "large": {"trust_gain": 75, "token_cost": 50}
}

@router.post("/dialogue/send-gift/", response_model=GiftResponse)
async def send_gift(
    request: GiftRequest,
    background_tasks: BackgroundTasks,
    current_user=Depends(get_current_user),
    db=Depends(get_db),
    dialogue_engine: AIDialogueEngine = Depends(lambda db=Depends(get_db): AIDialogueEngine(db))
):
    gift = GIFT_CONFIG.get(request.gift_type.value)
    if not gift: raise HTTPException(status_code=400, detail="Invalid gift type")

    unlocked_photo_url = None
    prompt_to_generate = None
    async with db.acquire() as connection:
        user_name = current_user["user_name"]
        async with connection.transaction():
            user = await connection.fetchrow("SELECT tokens FROM users WHERE id = $1 FOR UPDATE", current_user["user_id"])
            if user['tokens'] < gift["token_cost"]: raise HTTPException(status_code=403, detail="Not enough tokens")
            new_token_balance = user['tokens'] - gift["token_cost"]
            await connection.execute("UPDATE users SET tokens = $1 WHERE id = $2", new_token_balance, current_user["user_id"])
            user_state = await connection.fetchrow("SELECT trust_score, conversation_history FROM user_character_state WHERE user_id = $1 AND character_id = $2 FOR UPDATE", current_user["user_id"], request.character_id)
            new_trust_score = user_state["trust_score"] + gift["trust_gain"]
            await connection.execute("UPDATE user_character_state SET trust_score = $1 WHERE user_id = $2 AND character_id = $3", new_trust_score, current_user["user_id"], request.character_id)

        character = await connection.fetchrow("SELECT * FROM characters WHERE id = $1", request.character_id)
        new_layer = min((new_trust_score // 125), 8)

        # If this is a large gift for an intimate photo, trigger background generation
        if request.gift_type.value == "large" and request.intimacy_analysis and request.intimacy_analysis.get("intimacy_level") in ["intimate", "explicit"]:
            background_tasks.add_task(
                generate_intimate_photo_task,
                db,
                request.character_id,
                current_user["user_id"],
                request.intimacy_analysis
            )
            unlocked_photo_url = None # Photo will be sent via notification
        else:
            photo_to_unlock = await connection.fetchrow(
                """SELECT (elem->>'id')::uuid as id, elem->>'media_url' as url FROM layers l, LATERAL jsonb_array_elements(l.content_plan -> 'photo_prompts') elem WHERE l.character_id = $1 AND l.layer_order <= $2 AND (elem->>'is_locked')::boolean = true AND (elem->>'media_url') IS NOT NULL ORDER BY l.layer_order ASC, l.created_at ASC, (elem->>'id') ASC LIMIT 1;""",
                request.character_id, new_layer
            )

            if photo_to_unlock and photo_to_unlock['url']:
                print(f"--- Plan A: Found existing photo {photo_to_unlock['id']}. Unlocking and sending immediately. ---")
                await _unlock_photo(db, current_user["user_id"], photo_to_unlock['id'], request.character_id)
                unlocked_photo_url = photo_to_unlock['url']
            else:
                prompt_to_generate = await connection.fetchrow(
                    """SELECT (elem->>'id')::uuid as id, elem->>'prompt' as prompt, 'layer' as source, l.id as layer_id FROM layers l, LATERAL jsonb_array_elements(l.content_plan -> 'photo_prompts') elem WHERE l.character_id = $1 AND l.layer_order <= $2 AND (elem->>'is_locked')::boolean = true AND (elem->>'media_url') IS NULL ORDER BY l.layer_order ASC, l.created_at ASC, (elem->>'id') ASC LIMIT 1;""",
                    request.character_id, new_layer
                )
                if prompt_to_generate:
                    print(f"--- Plan B: Found prompt {prompt_to_generate['id']}. Generating synchronously. ---")
                    # This is now a blocking call
                    unlocked_photo_url = await _generate_and_unlock_photo(db, current_user["user_id"], request.character_id, prompt_to_generate['id'], prompt_to_generate['prompt'])
                else:
                    print(f"--- Plan C: No content to unlock. On-demand generation is not yet supported in sync mode. ---")
                    unlocked_photo_url = None # Placeholder

        conversation_history = json.loads(user_state["conversation_history"] or "[]")
        gift_response_dict = await dialogue_engine.generate_gift_response(
            character_data=dict(character), 
            user_name=user_name, 
            gift_type=request.gift_type.value,
            trust_score=new_trust_score, 
            conversation_history=conversation_history, 
            unlocked_photo_url=unlocked_photo_url,
            unlocked_photo_prompt=prompt_to_generate.get('prompt') if prompt_to_generate else None,
            intimacy_analysis=request.intimacy_analysis
        )
        full_character_response = (gift_response_dict['response'] + ' ' + ' '.join(gift_response_dict['message_parts'])).strip()
        await connection.execute("INSERT INTO messages (character_id, user_id, response, image_url, created_at) VALUES ($1, $2, $3, $4, NOW())", request.character_id, current_user["user_id"], full_character_response, unlocked_photo_url)

        return GiftResponse(new_trust_score=new_trust_score, new_token_balance=new_token_balance, message=f"You successfully sent a {request.gift_type.value} gift!", character_response=gift_response_dict["response"], response_parts=gift_response_dict["message_parts"], unlocked_photo_url=unlocked_photo_url)

async def _generate_and_unlock_photo(db, user_id: uuid.UUID, character_id: uuid.UUID, photo_id: uuid.UUID, prompt: str) -> Optional[str]:
    """Generates a photo, saves it, unlocks it, and returns the URL. Blocking."""
    import aiofiles, os
    try:
        comfy_service = ComfyService()
        async with db.acquire() as connection:
            character = await connection.fetchrow("SELECT avatar_url, visual_description FROM characters WHERE id = $1", character_id)
            if not character or not character['avatar_url']: 
                print(f"Character not found or no avatar_url for character_id: {character_id}")
                return None
            
            face_image_path = character['avatar_url'].lstrip('/')
            if not os.path.exists(face_image_path): 
                print(f"Avatar image not found at path: {face_image_path}")
                return None
                
            with open(face_image_path, "rb") as f: 
                face_image_bytes = f.read()
                
            base_description_json = character['visual_description']
            base_description_text = ""
            if base_description_json:
                try:
                    desc_data = json.loads(base_description_json)
                    base_description_text = ", ".join(f"{k.replace('_', ' ')} is {v}" for k, v in desc_data.items())
                except (json.JSONDecodeError, TypeError):
                    if isinstance(base_description_json, str): 
                        base_description_text = base_description_json

        final_prompt = f"{base_description_text}, {prompt}"
        print(f"Generating image with prompt: {final_prompt}")
        
        image_bytes = await comfy_service.generate_image_with_face(text_prompt=final_prompt, face_image_bytes=face_image_bytes)
        if not image_bytes: 
            print("Image generation failed - no bytes returned")
            return None

        upload_dir = f"uploads/{character_id}/content"
        os.makedirs(upload_dir, exist_ok=True)
        file_path = os.path.join(upload_dir, f"{photo_id}.png")
        
        async with aiofiles.open(file_path, 'wb') as f: 
            await f.write(image_bytes)
            
        media_url = f"/{file_path}"
        print(f"Image saved to: {media_url}")

        await _unlock_photo(db, user_id, photo_id, character_id)
        return media_url
        
    except Exception as e:
        print(f"Error in _generate_and_unlock_photo: {e}")
        return None

@router.get("/dialogue/history/{character_id}", response_model=HistoryResponse)
async def get_history(character_id: uuid.UUID, current_user=Depends(get_current_user), db=Depends(get_db)):
    async with db.acquire() as connection:
        messages = await connection.fetch(
            """SELECT content, image_url, created_at, role FROM (
                SELECT message as content, NULL as image_url, created_at, 'user' as role 
                FROM messages 
                WHERE user_id = $1 AND character_id = $2 AND message IS NOT NULL AND TRIM(COALESCE(message, '')) != ''
                UNION ALL 
                SELECT response as content, image_url, created_at, 'assistant' as role 
                FROM messages 
                WHERE user_id = $1 AND character_id = $2 AND response IS NOT NULL AND TRIM(COALESCE(response, '')) != ''
            ) as history 
            ORDER BY created_at ASC""",
            current_user["user_id"], character_id
        )
        user_state = await connection.fetchrow(
            "SELECT trust_score, current_layer FROM user_character_state WHERE user_id = $1 AND character_id = $2", 
            current_user["user_id"], character_id
        )
        character_info = await connection.fetchrow(
            "SELECT id, name, display_name, personality_type FROM characters WHERE id = $1", 
            character_id
        )
        if not user_state or not character_info: 
            raise HTTPException(status_code=404, detail="Character or user state not found")

    # Фильтрация пустых сообщений и форматирование дат
    valid_messages = []
    for m in messages:
        if m["content"] and m["content"].strip():
            valid_messages.append({
                "role": m["role"], 
                "content": m["content"], 
                "image_url": m["image_url"], 
                "created_at": m["created_at"].isoformat() if m["created_at"] else None
            })

    return HistoryResponse(
        messages=valid_messages, 
        trust_score=user_state["trust_score"] or 0, 
        current_layer=user_state["current_layer"] or 0, 
        character_info=dict(character_info)
    )
