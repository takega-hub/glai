from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional
from pydantic import BaseModel
import uuid

from api.auth.security import get_current_user
from api.database.connection import get_db

router = APIRouter(prefix="/notifications", tags=["notifications"])

class DeviceRegistrationRequest(BaseModel):
    device_token: str
    device_type: str # 'ios' or 'android'



class Notification(BaseModel):
    id: uuid.UUID
    message: str
    image_url: Optional[str]
    is_read: bool
    created_at: str

@router.get("/", response_model=List[Notification])
async def get_notifications(
    current_user=Depends(get_current_user),
    db=Depends(get_db)
):
    user_id = current_user["user_id"]
    async with db.acquire() as connection:
        records = await connection.fetch(
            """SELECT id, message, image_url, is_read, created_at 
               FROM notifications 
               WHERE user_id = $1 
               ORDER BY created_at DESC""",
            user_id
        )
        return [dict(r) for r in records]

@router.post("/{notification_id}/mark-as-read")
async def mark_as_read(
    notification_id: uuid.UUID,
    current_user=Depends(get_current_user),
    db=Depends(get_db)
):
    user_id = current_user["user_id"]
    async with db.acquire() as connection:
        await connection.execute(
            "UPDATE notifications SET is_read = TRUE WHERE id = $1 AND user_id = $2",
            notification_id, user_id
        )
    return {"message": "Notification marked as read."}

@router.post("/register-device")
async def register_device(
    request: DeviceRegistrationRequest,
    current_user=Depends(get_current_user),
    db=Depends(get_db)
):
    """Register a device token for push notifications."""
    user_id = current_user["user_id"]
    
    async with db.acquire() as connection:
        # Upsert logic: update if token exists, otherwise insert.
        await connection.execute(
            """ 
            INSERT INTO user_devices (user_id, device_token, device_type, updated_at)
            VALUES ($1, $2, $3, NOW())
            ON CONFLICT (device_token) DO UPDATE SET
            user_id = EXCLUDED.user_id,
            updated_at = NOW();
            """,
            user_id, request.device_token, request.device_type
        )
        
    return {"message": "Device registered successfully."}
