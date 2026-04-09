from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from datetime import datetime, timedelta
from typing import List, Optional
from api.auth.security import get_current_user, role_required
from api.database.connection import get_db
from api.services.ai_dialogue_v2 import AIDialogueEngine

router = APIRouter(prefix="/re-engagement", tags=["re-engagement"])


class ProactiveMessage(BaseModel):
    id: int
    character_id: int
    user_id: int
    message_type: str
    content: str
    image_url: Optional[str]
    trust_score_min: int
    last_sent: Optional[datetime]
    send_count: int
    is_active: bool

class ProactiveMessageCreate(BaseModel):
    character_id: int
    message_type: str
    content: str
    image_url: Optional[str]
    trust_score_min: int = 0
    trust_score_max: Optional[int]
    max_sends: int = 3
    is_active: bool = True

class ProactiveMessageUpdate(BaseModel):
    content: Optional[str]
    image_url: Optional[str]
    trust_score_min: Optional[int]
    trust_score_max: Optional[int]
    max_sends: Optional[int]
    is_active: Optional[bool]

class ReEngagementSettings(BaseModel):
    user_id: int
    is_enabled: bool
    frequency: str  # "daily", "weekly", "monthly"
    last_check: Optional[datetime]

@router.post("/create-proactive-message", response_model=ProactiveMessage)
async def create_proactive_message(
    message: ProactiveMessageCreate,
    current_user=Depends(role_required("content_manager")),
    db=Depends(get_db)
):
    """Create a new proactive message"""
    
    query = """
    INSERT INTO proactive_messages (character_id, message_type, content, image_url, trust_score_min, trust_score_max, max_sends, is_active, created_at)
    VALUES (:character_id, :message_type, :content, :image_url, :trust_score_min, :trust_score_max, :max_sends, :is_active, :created_at)
    RETURNING id, character_id, user_id, message_type, content, image_url, trust_score_min, last_sent, send_count, is_active
    """
    
    values = {
        "character_id": message.character_id,
        "message_type": message.message_type,
        "content": message.content,
        "image_url": message.image_url,
        "trust_score_min": message.trust_score_min,
        "trust_score_max": message.trust_score_max,
        "max_sends": message.max_sends,
        "is_active": message.is_active,
        "created_at": datetime.utcnow()
    }
    
    try:
        new_message = await db.fetch_one(query, values)
        return ProactiveMessage(**dict(new_message))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Could not create proactive message: {str(e)}"
        )

@router.get("/get-proactive-messages/{character_id}", response_model=List[ProactiveMessage])
async def get_proactive_messages(
    character_id: int,
    current_user=Depends(role_required("content_manager")),
    db=Depends(get_db)
):
    """Get all proactive messages for a character"""
    
    query = "SELECT * FROM proactive_messages WHERE character_id = :character_id ORDER BY created_at DESC"
    messages = await db.fetch_all(query, {"character_id": character_id})
    return [ProactiveMessage(**dict(msg)) for msg in messages]

@router.put("/update-proactive-message/{message_id}", response_model=ProactiveMessage)
async def update_proactive_message(
    message_id: int,
    message_update: ProactiveMessageUpdate,
    current_user=Depends(role_required("content_manager")),
    db=Depends(get_db)
):
    """Update a proactive message"""
    
    update_fields = []
    values = {"message_id": message_id}
    
    if message_update.content is not None:
        update_fields.append("content = :content")
        values["content"] = message_update.content
    
    if message_update.image_url is not None:
        update_fields.append("image_url = :image_url")
        values["image_url"] = message_update.image_url
    
    if message_update.trust_score_min is not None:
        update_fields.append("trust_score_min = :trust_score_min")
        values["trust_score_min"] = message_update.trust_score_min
    
    if message_update.trust_score_max is not None:
        update_fields.append("trust_score_max = :trust_score_max")
        values["trust_score_max"] = message_update.trust_score_max
    
    if message_update.max_sends is not None:
        update_fields.append("max_sends = :max_sends")
        values["max_sends"] = message_update.max_sends
    
    if message_update.is_active is not None:
        update_fields.append("is_active = :is_active")
        values["is_active"] = message_update.is_active
    
    if not update_fields:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No fields to update"
        )
    
    query = f"""
    UPDATE proactive_messages 
    SET {', '.join(update_fields)}
    WHERE id = :message_id
    RETURNING id, character_id, user_id, message_type, content, image_url, trust_score_min, last_sent, send_count, is_active
    """
    
    try:
        updated_message = await db.fetch_one(query, values)
        if not updated_message:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Proactive message not found"
            )
        return ProactiveMessage(**dict(updated_message))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Could not update proactive message: {str(e)}"
        )

@router.delete("/delete-proactive-message/{message_id}")
async def delete_proactive_message(
    message_id: int,
    current_user=Depends(role_required("content_manager")),
    db=Depends(get_db)
):
    """Delete a proactive message"""
    
    result = await db.execute(
        "DELETE FROM proactive_messages WHERE id = :message_id",
        {"message_id": message_id}
    )
    
    if result == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Proactive message not found"
        )
    
    return {"message": "Proactive message deleted successfully"}

@router.post("/trigger-re-engagement-check")
async def trigger_re_engagement_check(
    current_user=Depends(role_required("super_admin")),
    db=Depends(get_db),
    dialogue_engine: AIDialogueEngine = Depends(lambda db=Depends(get_db): AIDialogueEngine(db))
):
    """Manually trigger the re-engagement check for inactive users"""
    
    # Get inactive users (e.g., no messages in last 7 days)
    inactive_users = await db.fetch_all(
        """
        SELECT ucs.user_id, ucs.character_id, ucs.trust_score, u.username, u.email
        FROM user_character_state ucs
        JOIN users u ON ucs.user_id = u.id
        WHERE ucs.last_message_date < NOW() - INTERVAL '7 days'
        AND NOT EXISTS (
            SELECT 1 FROM proactive_messages pm 
            WHERE pm.user_id = ucs.user_id AND pm.character_id = ucs.character_id
            AND pm.last_sent >= NOW() - INTERVAL '7 days'
        )
        """
    )
    
    sent_messages = []
    for user in inactive_users:
        # Find a suitable proactive message
        proactive_message = await db.fetch_one(
            """
            SELECT * FROM proactive_messages 
            WHERE character_id = :character_id
            AND is_active = true
            AND trust_score_min <= :trust_score
            AND (trust_score_max IS NULL OR trust_score_max >= :trust_score)
            AND send_count < max_sends
            ORDER BY RANDOM()
            LIMIT 1
            """,
            {"character_id": user["character_id"], "trust_score": user["trust_score"]}
        )
        
        if proactive_message:
            # In a real implementation, you would send a push notification or email
            print(f"Sending proactive message to {user['email']}: {proactive_message['content']}")
            
            # Update proactive message stats
            await db.execute(
                """
                UPDATE proactive_messages 
                SET last_sent = :last_sent, send_count = send_count + 1 
                WHERE id = :message_id
                """,
                {"last_sent": datetime.utcnow(), "message_id": proactive_message["id"]}
            )
            
            sent_messages.append({
                "user_id": user["user_id"],
                "character_id": user["character_id"],
                "message": proactive_message["content"]
            })
    
    return {"message": f"Re-engagement check completed. Sent {len(sent_messages)} proactive messages.", "sent_messages": sent_messages}
