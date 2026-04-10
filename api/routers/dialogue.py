import uuid
import json

from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, Any, Optional, List

from api.auth.security import get_current_user
from api.database.connection import get_db
from api.services.ai_dialogue_v2 import AIDialogueEngine
from api.services.comfy_service import ComfyService
from api.tasks import _unlock_photo_in_db

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

class GiftResponse(BaseModel):
    new_trust_score: int
    new_token_balance: int
    message: str
    character_response: str
    character_response_parts: List[str]
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

        # Proactive Layer Update
        current_trust = user_state.get("trust_score", 0)
        current_layer = user_state.get("current_layer", 0)
        expected_layer = min((current_trust // 125), 8)

        if expected_layer > current_layer:
            await connection.execute(
                "UPDATE user_character_state SET current_layer = $1 WHERE user_id = $2 AND character_id = $3",
                expected_layer, current_user["user_id"], request.character_id
            )
            # Re-fetch user_state to have the most up-to-date info for the rest of the request
            user_state = await connection.fetchrow(
                "SELECT trust_score, conversation_history, current_layer FROM user_character_state WHERE user_id = $1 AND character_id = $2",
                current_user["user_id"], request.character_id
            )

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
    current_user=Depends(get_current_user),
    db=Depends(get_db),
    dialogue_engine: AIDialogueEngine = Depends(lambda db=Depends(get_db): AIDialogueEngine(db))
):
    gift = GIFT_CONFIG.get(request.gift_type.value)
    if not gift: raise HTTPException(status_code=400, detail="Invalid gift type")

    unlocked_photo_url = None
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
        
        # After gift, proactively update layer
        current_layer = user_state.get("current_layer", 0)
        expected_layer = min((new_trust_score // 125), 8)
        if expected_layer > current_layer:
            print(f"--- [Gift Layer Update] Trust: {new_trust_score}. Layer: {current_layer} -> {expected_layer}. Updating. ---")
            await connection.execute(
                "UPDATE user_character_state SET current_layer = $1 WHERE user_id = $2 AND character_id = $3",
                expected_layer, current_user["user_id"], request.character_id
            )

        # --- Unlock Content Logic ---
        # Priority 1: Try to unlock a ready-made (has media_url) teaser photo.
        photo_to_unlock = await connection.fetchrow(
            """SELECT id, media_url as url, prompt as description FROM content 
               WHERE character_id = $1 AND subtype = 'teaser' AND media_url IS NOT NULL
               AND id NOT IN (SELECT content_id FROM user_unlocked_content WHERE user_id = $2 AND character_id = $1)
               ORDER BY random() LIMIT 1""",
            request.character_id, current_user["user_id"]
        )

        if photo_to_unlock and photo_to_unlock['url']:
            print(f"--- Plan A (Teaser): Found existing teaser photo {photo_to_unlock['id']}. Unlocking and sending. ---")
            unlocked_photo_url = photo_to_unlock['url']
            # Unlock it for the user
            await connection.execute(
                "INSERT INTO user_unlocked_content (user_id, character_id, content_id) VALUES ($1, $2, $3) ON CONFLICT DO NOTHING",
                current_user["user_id"], request.character_id, photo_to_unlock['id']
            )
        else:
            # Priority 2: Try to unlock a ready-made (has media_url) layer photo.
            photo_to_unlock = await connection.fetchrow(
                """WITH potential_content AS (
                    SELECT elem->>'id' as id, elem->>'media_url' as url, elem->>'prompt' as description
                    FROM layers l, LATERAL jsonb_array_elements(l.content_plan -> 'photo_prompts') elem
                    WHERE l.character_id = $1 AND l.layer_order <= $2 AND (elem->>'media_url') IS NOT NULL
                )
                SELECT pc.id::uuid, pc.url, pc.description
                FROM potential_content pc
                WHERE pc.id::uuid NOT IN (SELECT content_id FROM user_unlocked_content WHERE user_id = $3 AND character_id = $1)
                ORDER BY random() LIMIT 1;""",
                request.character_id, expected_layer, current_user["user_id"]
            )

            if photo_to_unlock and photo_to_unlock['url']:
                print(f"--- Plan A (Layer): Found existing layer photo {photo_to_unlock['id']}. Unlocking and sending immediately. ---")
                unlocked_photo_url = photo_to_unlock['url']
                # This function handles both updating the JSON and adding to user_unlocked_content
                await _unlock_photo_in_db(db, photo_to_unlock['id'], request.character_id, current_user["user_id"])
            else:
                # Priority 3: Find a layer photo prompt to generate on-demand.
                prompt_to_generate = await connection.fetchrow(
                    """WITH potential_content AS (
                        SELECT elem->>'id' as id, elem->>'prompt' as prompt, elem->>'is_locked' as is_locked
                        FROM layers l, LATERAL jsonb_array_elements(l.content_plan -> 'photo_prompts') elem
                        WHERE l.character_id = $1 AND l.layer_order <= $2 AND (elem->>'media_url') IS NULL
                    )
                    SELECT pc.id::uuid, pc.prompt
                    FROM potential_content pc
                    WHERE pc.id IS NOT NULL AND (pc.is_locked IS NULL OR pc.is_locked = 'true')
                    ORDER BY random() LIMIT 1;""",
                    request.character_id, expected_layer
                )
                if prompt_to_generate:
                    print(f"--- Plan B (Layer): Found prompt {prompt_to_generate['id']}. Generating synchronously. ---")
                    unlocked_photo_url = await _generate_and_unlock_photo(db, request.character_id, prompt_to_generate['id'], prompt_to_generate['prompt'])
                else:
                    print(f"--- Plan C: No content to unlock. On-demand generation is not yet supported in sync mode. ---")
                    unlocked_photo_url = None # Placeholder

        conversation_history = json.loads(user_state["conversation_history"] or "[]")
        gift_response_dict = await dialogue_engine.generate_gift_response(
            character_data=dict(character), user_name=user_name, gift_type=request.gift_type.value,
            trust_score=new_trust_score, conversation_history=conversation_history, unlocked_photo_url=unlocked_photo_url,
            photo_prompt=photo_to_unlock.get('description') if photo_to_unlock else None
        )
        response_text = gift_response_dict.get("response") or ""
        extra_parts = gift_response_dict.get("message_parts") or []
        full_character_response = (response_text + ' ' + ' '.join(extra_parts)).strip()
        await connection.execute("INSERT INTO messages (character_id, user_id, response, image_url, created_at) VALUES ($1, $2, $3, $4, NOW())", request.character_id, current_user["user_id"], full_character_response, unlocked_photo_url)

        return GiftResponse(new_trust_score=new_trust_score, new_token_balance=new_token_balance, message=f"You successfully sent a {request.gift_type.value} gift!", character_response=gift_response_dict.get("response", ""), character_response_parts=gift_response_dict.get("message_parts", []), unlocked_photo_url=unlocked_photo_url)

async def _generate_and_unlock_photo(db, character_id: uuid.UUID, photo_id: uuid.UUID, prompt: str) -> Optional[str]:
    """Generates a photo, saves it, unlocks it, and returns the URL. Blocking."""
    import aiofiles, os
    comfy_service = ComfyService()
    async with db.acquire() as connection:
        character = await connection.fetchrow("SELECT avatar_url, visual_description FROM characters WHERE id = $1", character_id)
        if not character or not character['avatar_url']: return None
        face_image_path = character['avatar_url'].lstrip('/')
        if not os.path.exists(face_image_path): return None
        with open(face_image_path, "rb") as f: face_image_bytes = f.read()
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
    if not image_bytes: return None

    upload_dir = f"uploads/{character_id}/content"
    os.makedirs(upload_dir, exist_ok=True)
    file_path = os.path.join(upload_dir, f"{photo_id}.png")
    async with aiofiles.open(file_path, 'wb') as f: await f.write(image_bytes)
    media_url = f"/{file_path}"

    await _unlock_photo_in_db(db, photo_id, character_id, current_user["user_id"])
    return media_url

@router.get("/dialogue/history/{character_id}", response_model=HistoryResponse)
async def get_history(character_id: uuid.UUID, current_user=Depends(get_current_user), db=Depends(get_db)):
    async with db.acquire() as connection:
        character_info = await connection.fetchrow(
            "SELECT id, name, display_name, personality_type FROM characters WHERE id = $1", 
            character_id
        )
        if not character_info:
            raise HTTPException(status_code=404, detail="Character not found")

        user_state = await connection.fetchrow(
            "SELECT trust_score, current_layer, conversation_history FROM user_character_state WHERE user_id = $1 AND character_id = $2", 
            current_user["user_id"], character_id
        )
        
        if not user_state:
            # Create new state if none exists
            await connection.execute(
                "INSERT INTO user_character_state (user_id, character_id, trust_score, current_layer, conversation_history) VALUES ($1, $2, 0, 0, '[]')",
                current_user["user_id"], character_id
            )
            return HistoryResponse(
                messages=[], 
                trust_score=0, 
                current_layer=0, 
                character_info=dict(character_info)
            )

        messages_raw = await connection.fetch(
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

        # Фильтрация пустых сообщений и форматирование дат
        valid_messages = []
        for m in messages_raw:
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
