from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
import uuid
from datetime import datetime
from typing import Optional
import json

from api.database.connection import get_db

router = APIRouter(
    prefix="/admin/user-state",
    tags=["user_state_admin"],
)

class TrustScoreUpdate(BaseModel):
    user_id: str
    character_id: uuid.UUID
    new_trust_score: int

class UserCharacterState(BaseModel):
    user_id: uuid.UUID
    character_id: uuid.UUID
    trust_score: int
    current_layer: int
    layers_unlocked: list = []
    content_unlocked: list = []
    tokens_balance: int
    conversation_history: Optional[list] = None
    last_message_date: Optional[datetime] = None

@router.post("/update-trust-score", response_model=UserCharacterState)
async def update_trust_score(update_data: TrustScoreUpdate, db=Depends(get_db)):
    """
    Manually update the trust score for a user-character pair.
    """
    async with db.acquire() as connection:
        # Get current state
        user_state = await connection.fetchrow(
            "SELECT * FROM user_character_state WHERE user_id = $1 AND character_id = $2",
            update_data.user_id, update_data.character_id
        )

        if not user_state:
            # Check if user exists in database
            user_exists = await connection.fetchrow(
                "SELECT id FROM users WHERE id = $1",
                update_data.user_id
            )
            
            if not user_exists:
                # Create user record if it doesn't exist
                await connection.execute(
                    """INSERT INTO users (id, email, password_hash, role, created_at, last_active, status) 
                    VALUES ($1, $2, $3, $4, NOW(), NOW(), $5)""",
                    update_data.user_id,
                    f"{update_data.user_id}@temp.com",  # Temporary email
                    "temp_password_hash",  # Temporary password hash
                    "app_user",  # Default role
                    "active"  # Default status
                )
            
            # If the state doesn't exist, create it
            user_state = await connection.fetchrow(
                """INSERT INTO user_character_state (user_id, character_id, trust_score, current_layer) 
                VALUES ($1, $2, $3, 0) RETURNING *""",
                update_data.user_id, update_data.character_id, update_data.new_trust_score
            )
        else:
            # Update trust score
            user_state = await connection.fetchrow(
                "UPDATE user_character_state SET trust_score = $1 WHERE user_id = $2 AND character_id = $3 RETURNING *",
                update_data.new_trust_score, update_data.user_id, update_data.character_id
            )

        # Check for layer unlock
        character_layers = await connection.fetch(
            "SELECT layer_order, min_trust_score FROM layers WHERE character_id = $1 ORDER BY layer_order ASC",
            update_data.character_id
        )

        new_layer = user_state['current_layer']
        if new_layer < len(character_layers) - 1:
            next_layer_threshold = character_layers[new_layer + 1]['min_trust_score']
            if user_state['trust_score'] >= next_layer_threshold:
                new_layer += 1
                await connection.execute(
                    "UPDATE user_character_state SET current_layer = $1 WHERE user_id = $2 AND character_id = $3",
                    new_layer, update_data.user_id, update_data.character_id
                )
                user_state = await connection.fetchrow(
                    "SELECT * FROM user_character_state WHERE user_id = $1 AND character_id = $2",
                    update_data.user_id, update_data.character_id
                )

        user_state_dict = dict(user_state)
        if user_state_dict['conversation_history'] and isinstance(user_state_dict['conversation_history'], str):
            user_state_dict['conversation_history'] = json.loads(user_state_dict['conversation_history'])
        if user_state_dict['layers_unlocked'] and isinstance(user_state_dict['layers_unlocked'], str):
            user_state_dict['layers_unlocked'] = json.loads(user_state_dict['layers_unlocked'])
        if user_state_dict['content_unlocked'] and isinstance(user_state_dict['content_unlocked'], str):
            user_state_dict['content_unlocked'] = json.loads(user_state_dict['content_unlocked'])

        # Add tokens_balance to the response
        user_info = await connection.fetchrow("SELECT tokens FROM users WHERE id = $1", update_data.user_id)
        user_state_dict['tokens_balance'] = user_info['tokens'] if user_info else 0

        return UserCharacterState(**user_state_dict)
