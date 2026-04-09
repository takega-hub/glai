from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from api.auth.security import get_current_user
from passlib.context import CryptContext

router = APIRouter(prefix="/profile", tags=["profile"])

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class EmailNotifications(BaseModel):
    enabled: bool

class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str

@router.put("/notifications")
async def update_email_notifications(
    notifications: EmailNotifications,
    current_user=Depends(get_current_user)
):
    # Here you would typically update the user's notification preferences in the database
    print(f"User {current_user['user_id']} set email notifications to {notifications.enabled}")
    return {"status": "success"}

@router.put("/change-password")
async def change_password(
    password_request: ChangePasswordRequest,
    current_user=Depends(get_current_user)
):
    # Here you would typically verify the current password and update it in the database
    # For now, we'll just print the request
    print(f"User {current_user['user_id']} requested password change")
    
    # TODO: Implement actual password verification and update logic
    # 1. Verify current password matches the one in database
    # 2. Hash the new password
    # 3. Update the password in the database
    
    return {"status": "success", "message": "Password changed successfully"}
