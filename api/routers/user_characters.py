from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional
import logging
import json
from pydantic import BaseModel
import uuid
from api.database.connection import get_db
from api.auth.security import get_current_user

router = APIRouter(prefix="/characters", tags=["user_characters"])

class UserCharacterResponse(BaseModel):
    id: str
    name: str
    display_name: str
    avatar_url: Optional[str]
    personality_type: Optional[str]
    age: Optional[int]
    archetype: Optional[str]
    biography: Optional[str]
    status: str
    trust_score: int
    is_hot: bool

class ContentPreviewItem(BaseModel):
    id: str
    thumbnail_url: Optional[str]
    is_locked: bool

class UserCharacterWithStateResponse(BaseModel):
    id: str
    name: str
    display_name: str
    avatar_url: Optional[str]
    personality_type: Optional[str]
    age: Optional[int]
    archetype: Optional[str]
    biography: Optional[str]
    status: str
    trust_score: int
    current_layer: int
    last_interaction: Optional[str]
    content_preview: List[ContentPreviewItem] = []
    is_hot: bool
    subscribers: int

@router.get("", response_model=List[UserCharacterWithStateResponse])
async def get_user_characters(
    current_user=Depends(get_current_user),
    db=Depends(get_db)
):
    """
    Get all characters available to the user with their current state (trust score, layer, etc.)
    and a preview of their content.
    """
    user_id = current_user['user_id']
    
    query = """
        SELECT 
            c.id, c.name, c.display_name, c.avatar_url, c.archetype, c.biography, c.age, c.status, c.is_hot,
            COALESCE(uct.trust_score, 0) as trust_score,
            uct.current_layer,
            uct.last_message_date as last_interaction,
            media.content_preview,
            COALESCE(sub.subscriber_count, 0) as subscribers
        FROM characters c
        LEFT JOIN user_character_state uct ON c.id = uct.character_id AND uct.user_id = $1
        LEFT JOIN LATERAL (
            SELECT json_agg(cp.content_item) as content_preview
            FROM (
                SELECT
                    jsonb_build_object(
                        'id', (elem ->> 'id'),
                        'thumbnail_url', (elem ->> 'media_url'),
                        'is_locked', (COALESCE(l.min_trust_score, 0) > COALESCE(uct.trust_score, 0))
                    ) as content_item
                FROM layers l,
                     jsonb_array_elements(l.content_plan -> 'photo_prompts') elem
                WHERE l.character_id = c.id AND elem ->> 'media_url' IS NOT NULL
                UNION ALL
                SELECT
                    jsonb_build_object(
                        'id', (elem ->> 'id'),
                        'thumbnail_url', (elem ->> 'media_url'),
                        'is_locked', (COALESCE(l.min_trust_score, 0) > COALESCE(uct.trust_score, 0))
                    ) as content_item
                FROM layers l,
                     jsonb_array_elements(l.content_plan -> 'video_prompts') elem
                WHERE l.character_id = c.id AND elem ->> 'media_url' IS NOT NULL
                LIMIT 4
            ) cp
        ) media ON true
        LEFT JOIN LATERAL (
            SELECT COUNT(DISTINCT u.user_id) as subscriber_count
            FROM user_character_state u
            WHERE u.character_id = c.id
        ) sub ON true
        WHERE c.status = 'active'
        ORDER BY uct.last_message_date DESC NULLS LAST, c.created_at DESC
    """
    


    characters = await db.fetch(query, user_id)

    # Format the response
    result = []
    for char in characters:
        content_preview = char["content_preview"]
        if isinstance(content_preview, str):
            content_preview = json.loads(content_preview)

        character_data = {
            "id": str(char["id"]),
            "name": char["name"],
            "display_name": char["display_name"],
            "avatar_url": char["avatar_url"],
            "personality_type": char["archetype"],  # Using archetype as personality_type for now
            "age": char["age"],
            "archetype": char["archetype"],
            "biography": char["biography"],
            "status": char["status"],
            "trust_score": char["trust_score"],
            "current_layer": char["current_layer"] or 0,
            "last_interaction": char["last_interaction"].isoformat() if char["last_interaction"] else None,
            "content_preview": content_preview or [],
            "is_hot": char["is_hot"],
            "subscribers": char["subscribers"]
        }
        result.append(UserCharacterWithStateResponse(**character_data))
    
    return result

@router.get("/{character_id}", response_model=UserCharacterResponse)
async def get_user_character(
    character_id: uuid.UUID,
    current_user=Depends(get_current_user),
    db=Depends(get_db)
):
    """
    Get a specific character by ID (user-facing)
    """
    user_id = current_user['user_id']
    query = """
        SELECT 
            c.id, c.name, c.display_name, c.avatar_url, c.archetype, c.biography, c.age, c.status, c.is_hot,
            COALESCE(uct.trust_score, 0) as trust_score
        FROM characters c
        LEFT JOIN user_character_state uct ON c.id = uct.character_id AND uct.user_id = $2
        WHERE c.id = $1 AND c.status = 'active'
    """
    
    character = await db.fetchrow(query, character_id, user_id)
    
    if not character:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Character not found or not available"
        )
    
    return UserCharacterResponse(
        id=str(character["id"]),
        name=character["name"],
        display_name=character["display_name"],
        avatar_url=character["avatar_url"],
        personality_type=character["archetype"],
        age=character["age"],
        archetype=character["archetype"],
        biography=character["biography"],
        status=character["status"],
        trust_score=character["trust_score"],
        is_hot=character["is_hot"]
    )