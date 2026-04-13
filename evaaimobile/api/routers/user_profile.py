from fastapi import APIRouter, Depends, HTTPException, status, File, UploadFile
import aiofiles
import os
from pydantic import BaseModel
from typing import Optional
import uuid
from datetime import datetime

from api.database.connection import get_db
from api.auth.security import get_current_user

router = APIRouter(
    prefix="/user/profile",
    tags=["user_profile"],
)

class UserProfile(BaseModel):
    display_name: Optional[str] = None
    about: Optional[str] = None
    avatar_url: Optional[str] = None

class UserProfileResponse(UserProfile):
    user_id: uuid.UUID
    updated_at: datetime

@router.get("", response_model=UserProfileResponse)
async def get_user_profile(db=Depends(get_db), current_user=Depends(get_current_user)):
    """Get the current user's profile"""
    user_id = current_user['user_id']
    profile = await db.fetchrow(
        "SELECT * FROM user_profiles WHERE user_id = $1",
        uuid.UUID(user_id)
    )
    if not profile:
        # Create a default profile if one doesn't exist
        profile = await db.fetchrow(
            "INSERT INTO user_profiles (user_id) VALUES ($1) RETURNING *",
            uuid.UUID(user_id)
        )
    return dict(profile)

@router.put("", response_model=UserProfileResponse)
async def update_user_profile(profile_data: UserProfile, db=Depends(get_db), current_user=Depends(get_current_user)):
    """Update the current user's profile"""
    user_id = current_user['user_id']
    
    # Construct the update query dynamically
    update_fields = []
    update_values = []
    
    if profile_data.display_name is not None:
        update_fields.append("display_name = $2")
        update_values.append(profile_data.display_name)
    
    if profile_data.about is not None:
        update_fields.append(f"about = ${len(update_values) + 2}")
        update_values.append(profile_data.about)
        
    if profile_data.avatar_url is not None:
        update_fields.append(f"avatar_url = ${len(update_values) + 2}")
        update_values.append(profile_data.avatar_url)

    if not update_fields:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No fields to update")

    update_query = f"""
    UPDATE user_profiles
    SET {', '.join(update_fields)}, updated_at = NOW()
    WHERE user_id = $1
    RETURNING *
    """
    
    updated_profile = await db.fetchrow(
        update_query,
        uuid.UUID(user_id),
        *update_values
    )
    
    if not updated_profile:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Profile not found")
        
    return dict(updated_profile)


@router.post("/avatar")
async def upload_avatar(
    file: UploadFile = File(...),
    db=Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Upload a new avatar for the current user"""
    user_id = current_user["user_id"]

    # Create uploads directory if it doesn't exist
    upload_dir = "uploads/avatars"
    os.makedirs(upload_dir, exist_ok=True)

    # Generate a unique filename
    file_extension = file.filename.split(".")[-1]
    filename = f"{user_id}.{file_extension}"
    file_path = os.path.join(upload_dir, filename)

    # Save the file
    try:
        async with aiofiles.open(file_path, "wb") as out_file:
            content = await file.read()
            await out_file.write(content)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error uploading file: {str(e)}",
        )

    # Update the user's profile with the new avatar URL
    avatar_url = f"/{file_path}"
    update_query = """
    UPDATE user_profiles
    SET avatar_url = $2, updated_at = NOW()
    WHERE user_id = $1
    RETURNING *
    """

    updated_profile = await db.fetchrow(
        update_query, uuid.UUID(user_id), avatar_url
    )

    if not updated_profile:
        # If no profile exists, create one
        updated_profile = await db.fetchrow(
            """
            INSERT INTO user_profiles (user_id, avatar_url) VALUES ($1, $2)
            RETURNING *
            """,
            uuid.UUID(user_id),
            avatar_url,
        )

    return dict(updated_profile)
