from fastapi import APIRouter, Depends
from api.auth.security import get_current_user
from api.database.connection import get_db

router = APIRouter(prefix="/user-analytics", tags=["user-analytics"])

@router.get("/")
async def get_user_analytics(current_user=Depends(get_current_user), db=Depends(get_db)):
    user_id = current_user['user_id']

    total_messages = await db.fetchval("SELECT COUNT(*) FROM messages WHERE user_id = $1", user_id)
    total_characters_interacted = await db.fetchval("SELECT COUNT(DISTINCT character_id) FROM messages WHERE user_id = $1", user_id)
    total_tokens_spent = await db.fetchval("SELECT COUNT(*) FROM transactions WHERE user_id = $1 AND type = 'message_sent'", user_id)
    unlocked_content = await db.fetchval("SELECT COUNT(*) FROM transactions WHERE user_id = $1 AND type = 'content_unlock'", user_id)

    return {
        "total_messages": total_messages or 0,
        "total_characters_interacted": total_characters_interacted or 0,
        "total_tokens_spent": abs(total_tokens_spent or 0),
        "unlocked_content": unlocked_content or 0,
    }
