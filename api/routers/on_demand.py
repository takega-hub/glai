from fastapi import APIRouter, Depends, HTTPException, status, Form
from pydantic import BaseModel
from datetime import datetime
from typing import Optional
from api.auth.security import get_current_user
from api.database.connection import get_db
from api.services.ai_dialogue_v2 import AIDialogueEngine

router = APIRouter(prefix="/on-demand", tags=["on-demand"])
class OnDemandRequest(BaseModel):
    character_id: int
    prompt: str
    style: Optional[str] = "realistic"

class OnDemandResponse(BaseModel):
    id: int
    user_id: int
    character_id: int
    prompt: str
    image_url: str
    token_cost: int
    status: str
    created_at: datetime

@router.post("/generate-image", response_model=OnDemandResponse)
async def generate_on_demand_image(
    request: OnDemandRequest,
    current_user=Depends(get_current_user),
    db=Depends(get_db),
    dialogue_engine: AIDialogueEngine = Depends(lambda db=Depends(get_db): AIDialogueEngine(db))
):
    """Generate an on-demand image based on user prompt and trust score"""
    
    # Get character data
    character = await db.fetch_one(
        "SELECT * FROM characters WHERE id = :character_id",
        {"character_id": request.character_id}
    )
    
    if not character:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Character not found"
        )
    
    # Get user trust score and token balance
    user_state = await db.fetch_one(
        "SELECT trust_score, tokens FROM user_character_state WHERE user_id = :user_id AND character_id = :character_id",
        {"user_id": current_user["user_id"], "character_id": request.character_id}
    )
    
    if not user_state:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User character state not found"
        )
    
    # Generate image prompt with trust score adjustments
    prompt_data = await dialogue_engine.generate_on_demand_image_prompt(
        user_request=request.prompt,
        character_data=dict(character),
        trust_score=user_state["trust_score"],
        style=request.style
    )
    
    # Check token balance
    token_cost = prompt_data["estimated_tokens"]
    if user_state["tokens"] < token_cost:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Insufficient tokens. Required: {token_cost}, Available: {user_state['tokens']}"
        )
    
    # In a real implementation, you would:
    # 1. Call an AI image generation service with the generated prompt
    # 2. Save the generated image to a storage service (e.g., S3)
    # 3. Get the image URL
    
    # For now, we'll use a placeholder URL
    image_url = f"/images/generated/{character['name']}_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}.png"
    
    # Deduct tokens from user
    await db.execute(
        "UPDATE users SET tokens = tokens - :cost WHERE id = :user_id",
        {"cost": token_cost, "user_id": current_user["user_id"]}
    )
    
    # Create on-demand generation record
    query = """
    INSERT INTO on_demand_generations (user_id, character_id, prompt, image_url, trust_level, token_cost, status, created_at)
    VALUES (:user_id, :character_id, :prompt, :image_url, :trust_level, :token_cost, 'completed', :created_at)
    RETURNING id, user_id, character_id, prompt, image_url, token_cost, status, created_at
    """
    
    values = {
        "user_id": current_user["user_id"],
        "character_id": request.character_id,
        "prompt": prompt_data["prompt"],
        "image_url": image_url,
        "trust_level": prompt_data["trust_level"],
        "token_cost": token_cost,
        "created_at": datetime.utcnow()
    }
    
    try:
        generation_record = await db.fetch_one(query, values)
        
        # Record transaction
        await db.execute(
            """
            INSERT INTO transactions (user_id, type, token_amount, description, balance_after, created_at)
            VALUES (:user_id, 'on_demand_generation', :amount, :description, 
                   (SELECT tokens FROM users WHERE id = :user_id), :created_at)
            """,
            {
                "user_id": current_user["user_id"],
                "amount": -token_cost,
                "description": f"On-demand image generation for {character['name']}",
                "created_at": datetime.utcnow()
            }
        )
        
        return OnDemandResponse(**dict(generation_record))
    except Exception as e:
        # Refund tokens if record creation fails
        await db.execute(
            "UPDATE users SET tokens = tokens + :cost WHERE id = :user_id",
            {"cost": token_cost, "user_id": current_user["user_id"]}
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Could not process on-demand generation: {str(e)}"
        )
