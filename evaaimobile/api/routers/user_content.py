from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
import uuid

from api.database.connection import get_db
from api.auth.security import get_current_user

router = APIRouter(
    prefix="/content",
    tags=["content"],
)

class ContentItemResponse(BaseModel):
    id: str
    type: str
    media_url: Optional[str]
    thumbnail_url: Optional[str]
    description: Optional[str]
    is_locked: bool
    unlock_requirement: str

class ContentGalleryResponse(BaseModel):
    character: dict
    content: List[ContentItemResponse]

import os

def get_optimized_urls(original_url: str):
    if not original_url:
        return original_url, original_url

    base, ext = os.path.splitext(original_url)
    
    # In our case, the files are in the `uploads` folder, which is mapped to the `/uploads` path in the URL
    # We need to construct the file path on the server to check for existence.
    # The URL is relative to the domain, so we need to map it to the filesystem.
    # This is a bit of a hack, but it's the simplest way to do it without a more complex asset management system.
    # /uploads/path/to/image.png -> /opt/EVA_AI/uploads/path/to/image.png
    file_path_base = "/opt/EVA_AI" + base

    optimized_path = f"{file_path_base}_optimized.webp"
    thumbnail_path = f"{file_path_base}_thumbnail.webp"

    # We need to construct the URL back from the path
    optimized_url = f"{base}_optimized.webp"
    thumbnail_url = f"{base}_thumbnail.webp"

    # Check if the optimized files exist on the filesystem
    # This is not ideal as it couples the API to the filesystem, but it's a pragmatic solution for now.
    # A better solution would be to store the optimized URLs in the database when they are created.
    if os.path.exists(optimized_path):
        media_url = optimized_url
    else:
        media_url = original_url

    if os.path.exists(thumbnail_path):
        thumb_url = thumbnail_url
    elif os.path.exists(optimized_path):
        thumb_url = optimized_url # Fallback to optimized if thumbnail doesn't exist
    else:
        thumb_url = original_url

    return media_url, thumb_url

@router.get("/character/{character_id}", response_model=ContentGalleryResponse)
async def get_character_content(
    character_id: uuid.UUID,
    db=Depends(get_db),
    current_user=Depends(get_current_user)
):
    """
    Get content gallery for a specific character.
    Content is unlocked by being sent in chat, not by trust level.
    """
    # 1. Get character info
    character = await db.fetchrow(
        "SELECT id, name, display_name, avatar_url, archetype FROM characters WHERE id = $1", 
        character_id
    )
    if not character:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Character not found")

    # 2. Get all content for the character and check unlock status for the current user
    query = """
        WITH all_photos AS (
            -- Teaser Photos
            SELECT id, type, media_url as url, prompt AS description, created_at, 0 as layer_order
            FROM content
            WHERE character_id = $1 AND subtype = 'teaser' AND media_url IS NOT NULL
            UNION ALL
            -- Layer Photos
            SELECT (elem->>'id')::uuid, 'photo', elem->>'media_url', elem->>'prompt', l.created_at, l.layer_order
            FROM layers l, jsonb_array_elements(l.content_plan -> 'photo_prompts') elem
            WHERE l.character_id = $1 AND elem->>'media_url' IS NOT NULL
        )
        SELECT
            p.id,
            p.type,
            p.url,
            p.description,
            (uuc.content_id IS NULL) AS is_locked -- if it's not in user_unlocked_content, it's locked
        FROM all_photos p
        LEFT JOIN user_unlocked_content uuc ON uuc.content_id = p.id AND uuc.user_id = $2 AND uuc.character_id = $1
        ORDER BY p.layer_order ASC, p.created_at ASC;
    """
    
    all_content_records = await db.fetch(query, character_id, current_user["user_id"])

    # 3. Format the response
    content_list = []
    for item in all_content_records:
        is_avatar = item['url'] == character['avatar_url']
        is_locked = item['is_locked'] and not is_avatar

        media_url, thumbnail_url = get_optimized_urls(item['url'])

        content_list.append({
            "id": str(item['id']),
            "type": item['type'],
            "media_url": media_url,
            "thumbnail_url": thumbnail_url,
            "description": item['description'],
            "is_locked": is_locked,
            "unlock_requirement": "Аватар" if is_avatar else ("Откроется в диалоге" if is_locked else "Доступно")
        })

    return {
        "character": dict(character),
        "content": content_list
    }