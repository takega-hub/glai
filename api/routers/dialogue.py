import uuid
import json

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from typing import Dict, Any, Optional, List

from api.auth.security import get_current_user
from api.database.connection import get_db
from api.services.ai_dialogue_v2 import AIDialogueEngine
from api.services.comfy_service import ComfyService
from api.tasks import _unlock_photo_in_db
from api.services.notification_service import notification_service

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
    proposal_details: Optional[Dict] = None

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
    background_tasks: BackgroundTasks,
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
            user_name=current_user["user_name"],
            user_id=current_user["user_id"]
        )

        # --- Unlock Photo Logic ---
        image_url_to_unlock = response_data.get("image_url")
        if image_url_to_unlock:
            import os
            try:
                filename = os.path.basename(image_url_to_unlock)
                photo_id_str = os.path.splitext(filename)[0].replace("_optimized", "")
                photo_id = uuid.UUID(photo_id_str)
                
                print(f"--- Unlocking photo {photo_id} for user {current_user['user_id']} ---")
                await connection.execute(
                    "INSERT INTO user_unlocked_content (user_id, character_id, content_id) VALUES ($1, $2, $3) ON CONFLICT DO NOTHING",
                    current_user["user_id"], request.character_id, photo_id
                )
            except (ValueError, TypeError) as e:
                print(f"!!! Could not parse photo ID from URL '{image_url_to_unlock}': {e} !!!")
        # --- End Unlock Photo Logic ---

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

        # 4. Update trust score, capping at 1000
        trust_change = response_data.get("trust_score_change", 0)
        new_trust_score = min(user_state["trust_score"] + trust_change, 1000)

        # 5. Save the fully updated history and trust score
        await connection.execute(
            "UPDATE user_character_state SET conversation_history = $1, trust_score = $2 WHERE user_id = $3 AND character_id = $4",
            json.dumps(conversation_history), new_trust_score, current_user["user_id"], request.character_id
        )
        
        # 5. Decrement tokens (only once per user message)
        await connection.execute("UPDATE users SET tokens = tokens - 1 WHERE id = $1", current_user["user_id"])

        # 6. Send push notification in background
        background_tasks.add_task(
            notification_service.send_push_notification,
            db,
            str(current_user["user_id"]),
            title=character["display_name"] or character["name"],
            body=response_data["response"],
            data={
                "character_id": str(request.character_id),
                "type": "new_message"
            }
        )

    return MessageResponse(
        response=response_data.get("response", ""),
        response_parts=response_data.get("message_parts", []),
        image_url=response_data.get("image_url")
    )

GIFT_CONFIG = {
    "small": {"trust_gain": 10, "token_cost": 10},
    "medium": {"trust_gain": 30, "token_cost": 25},
    "large": {"trust_gain": 75, "token_cost": 50}
}

@router.post("/dialogue/send-gift", response_model=GiftResponse)
async def send_gift(
    request: GiftRequest,
    background_tasks: BackgroundTasks,
    current_user=Depends(get_current_user),
    db=Depends(get_db),
    dialogue_engine: AIDialogueEngine = Depends(lambda db=Depends(get_db): AIDialogueEngine(db))
):
    gift = GIFT_CONFIG.get(request.gift_type.value)
    if not gift: raise HTTPException(status_code=400, detail="Invalid gift type")

    async with db.acquire() as connection:
        user_name = current_user["user_name"]
        async with connection.transaction():
            user = await connection.fetchrow("SELECT tokens FROM users WHERE id = $1 FOR UPDATE", current_user["user_id"])
            if user['tokens'] < gift["token_cost"]: raise HTTPException(status_code=403, detail="Not enough tokens")
            new_token_balance = user['tokens'] - gift["token_cost"]
            await connection.execute("UPDATE users SET tokens = $1 WHERE id = $2", new_token_balance, current_user["user_id"])
            
            user_state = await connection.fetchrow("SELECT trust_score, conversation_history, current_layer FROM user_character_state WHERE user_id = $1 AND character_id = $2 FOR UPDATE", current_user["user_id"], request.character_id)
            
            # Large gifts do not increase trust; they are for transactions.
            new_trust_score = user_state["trust_score"]
            if request.gift_type != 'large':
                new_trust_score = min(user_state["trust_score"] + gift["trust_gain"], 1000)
            
            await connection.execute("UPDATE user_character_state SET trust_score = $1 WHERE user_id = $2 AND character_id = $3", new_trust_score, current_user["user_id"], request.character_id)

        character = await connection.fetchrow("SELECT * FROM characters WHERE id = $1", request.character_id)
        conversation_history = json.loads(user_state.get("conversation_history") or "[]")

        # --- CONTEXTUAL GIFT LOGIC ---
        if request.gift_type == 'large':
            print("--- [CONTEXTUAL GIFT] Large gift received. Checking context for on-demand generation. ---")
            
            user_intent = "a very intimate and explicit photo"
            if request.proposal_details and request.proposal_details.get("user_intent"):
                user_intent = request.proposal_details.get("user_intent")
            else:
                # Fallback: search history for the last user message that might be a prompt
                for message in reversed(conversation_history):
                    if message.get("role") == "user":
                        user_intent = message.get("content")
                        break

            generation_prompt_data = await dialogue_engine.generate_on_demand_image_prompt(
                user_request=user_intent,
                character_data=dict(character),
                trust_score=new_trust_score,
                style="photorealistic",
                conversation_history=conversation_history
            )
            generation_prompt = generation_prompt_data.get("prompt")
            if not generation_prompt:
                raise HTTPException(status_code=500, detail="Failed to generate a prompt for the image.")

            photo_id = uuid.uuid4()
            from api.tasks import generate_and_send_photo_task
            background_tasks.add_task(
                generate_and_send_photo_task,
                db,
                character_id=request.character_id,
                user_id=current_user["user_id"],
                photo_id=photo_id,
                user_prompt=generation_prompt
            )
            
            confirmation_text = "Ммм, какой щедрый подарок... Я уже готовлю для тебя нечто особенное. Скоро ты всё увидишь..."
            await connection.execute("INSERT INTO messages (character_id, user_id, response, created_at) VALUES ($1, $2, $3, NOW())", request.character_id, current_user["user_id"], confirmation_text)

            return GiftResponse(
                new_trust_score=new_trust_score,
                new_token_balance=new_token_balance,
                message="You successfully initiated a custom photo generation!",
                character_response=confirmation_text,
                character_response_parts=[],
                unlocked_photo_url=None
            )
        
        # --- STANDARD GIFT LOGIC (Small/Medium) ---
        unlocked_photo_url = None
        current_layer = user_state.get("current_layer", 0)
        expected_layer = min((new_trust_score // 125), 8)
        if expected_layer > current_layer:
            print(f"--- [Gift Layer Update] Trust: {new_trust_score}. Layer: {current_layer} -> {expected_layer}. Updating. ---")
            await connection.execute(
                "UPDATE user_character_state SET current_layer = $1 WHERE user_id = $2 AND character_id = $3",
                expected_layer, current_user["user_id"], request.character_id
            )

        # Standard content unlock logic for small/medium gifts
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
            await connection.execute(
                "INSERT INTO user_unlocked_content (user_id, character_id, content_id) VALUES ($1, $2, $3) ON CONFLICT DO NOTHING",
                current_user["user_id"], request.character_id, photo_to_unlock['id']
            )
        else:
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
                await _unlock_photo_in_db(db, photo_to_unlock['id'], request.character_id, current_user["user_id"])
            else:
                print(f"--- Plan B/C Failure: No content to unlock or generate for small/medium gift. ---")
                unlocked_photo_url = None

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

class PhotoGenerationRequest(BaseModel):
    character_id: uuid.UUID
    intimacy_analysis: Dict

@router.post("/dialogue/generate-photo-from-proposal")
async def generate_photo_from_proposal(
    request: PhotoGenerationRequest,
    current_user=Depends(get_current_user),
    db=Depends(get_db),
    dialogue_engine: AIDialogueEngine = Depends(lambda db=Depends(get_db): AIDialogueEngine(db))
):
    # Define cost for on-demand generation
    token_cost = 50 # Corresponds to a "large" gift

    async with db.acquire() as connection:
        async with connection.transaction():
            # 1. Deduct tokens
            user = await connection.fetchrow("SELECT tokens FROM users WHERE id = $1 FOR UPDATE", current_user["user_id"])
            if user['tokens'] < token_cost:
                raise HTTPException(status_code=403, detail="Not enough tokens for photo generation.")
            new_token_balance = user['tokens'] - token_cost
            await connection.execute("UPDATE users SET tokens = $1 WHERE id = $2", new_token_balance, current_user["user_id"])

            # 2. Trigger background generation task
            character = await connection.fetchrow("SELECT * FROM characters WHERE id = $1", request.character_id)
            user_state = await connection.fetchrow("SELECT trust_score, conversation_history FROM user_character_state WHERE user_id = $1 AND character_id = $2", current_user["user_id"], request.character_id)

            # Use the AI service to generate a high-quality prompt based on the original request
            generation_prompt_data = await dialogue_engine.generate_on_demand_image_prompt(
                user_request=request.intimacy_analysis.get("user_intent", "a beautiful photo"),
                character_data=dict(character),
                trust_score=user_state["trust_score"],
                style="photorealistic",
                conversation_history=json.loads(user_state.get("conversation_history") or "[]")
            )

            generation_prompt = generation_prompt_data.get("prompt")
            if not generation_prompt:
                raise HTTPException(status_code=500, detail="Failed to generate a prompt for the image.")

            # Create a new unique ID for this on-demand content
            photo_id = uuid.uuid4()

            # Use the AI service to generate a high-quality prompt based on the original request
            generation_prompt_data = await dialogue_engine.generate_on_demand_image_prompt(
                user_request=request.intimacy_analysis.get("user_intent", "a beautiful photo"),
                character_data=dict(character),
                trust_score=user_state["trust_score"],
                style="photorealistic",
                conversation_history=json.loads(user_state.get("conversation_history") or "[]")
            )

            generation_prompt = generation_prompt_data.get("prompt")
            if not generation_prompt:
                raise HTTPException(status_code=500, detail="Failed to generate a prompt for the image.")

            # Create a new unique ID for this on-demand content
            photo_id = uuid.uuid4()

            from api.tasks import generate_and_send_photo_task
            background_tasks = BackgroundTasks()
            background_tasks.add_task(
                generate_and_send_photo_task,
                character_id=request.character_id,
                user_id=current_user["user_id"],
                photo_id=photo_id,
                user_prompt=generation_prompt
            )
            
            # Return a confirmation to the user
            return {"message": "Your unique photo is being generated! It will appear in the chat shortly.", "new_token_balance": new_token_balance}


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

@router.get("/characters/{character_id}/personal-gallery")
async def get_personal_gallery(character_id: uuid.UUID, current_user=Depends(get_current_user)):
    import os
    user_id = current_user["user_id"]
    gallery_dir = f"uploads/{character_id}/Personal/{user_id}"
    
    if not os.path.exists(gallery_dir) or not os.path.isdir(gallery_dir):
        return []

    try:
        # Get all file paths and sort them by modification time (newest first)
        files = [os.path.join(gallery_dir, f) for f in os.listdir(gallery_dir)]
        files.sort(key=lambda x: os.path.getmtime(x), reverse=True)
        
        # Return the web-accessible paths
        return [f"/{f}" for f in files]
    except Exception as e:
        print(f"!!! Error reading personal gallery for user {user_id}: {e} !!!")
        raise HTTPException(status_code=500, detail="Could not retrieve personal gallery.")
