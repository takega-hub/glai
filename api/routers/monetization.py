from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from pydantic import BaseModel
from datetime import datetime
from typing import List, Optional, Union
import uuid
import asyncpg
from api.auth.security import get_current_user
from api.database.connection import get_db

from api.tasks import generate_and_send_photo_task

router = APIRouter(prefix="/monetization", tags=["monetization"])

class TokenPackage(BaseModel):
    id: int
    name: str
    token_amount: int
    price_usd: float
    bonus_tokens: int = 0
    is_active: bool = True

class GiftItem(BaseModel):
    id: int
    name: str
    description: str
    token_cost: int
    image_url: str
    category: str  # "virtual", "premium", "exclusive"
    trust_score_required: int = 0
    is_active: bool = True

class PurchaseTokensRequest(BaseModel):
    package_id: int
    payment_method: str = "stripe"  # stripe, paypal, etc.

class SendGiftRequest(BaseModel):
    recipient_id: Union[int, uuid.UUID]
    gift_id: int
    message: Optional[str] = None
    user_prompt: Optional[str] = None # For photo generation

class TransactionResponse(BaseModel):
    id: int
    user_id: int
    type: str  # "purchase", "gift_sent", "gift_received", "content_unlock"
    amount: int
    description: str
    created_at: datetime
    balance_after: int

class UserBalanceResponse(BaseModel):
    user_id: int
    balance: int
    total_spent: float
    total_received: int

# Token packages management
@router.get("/token-packages", response_model=List[TokenPackage])
async def get_token_packages(db=Depends(get_db)):
    """Get available token packages"""
    query = "SELECT * FROM token_packages WHERE is_active = true ORDER BY token_amount"
    packages = await db.fetch_all(query)
    return [TokenPackage(**dict(pkg)) for pkg in packages]

@router.post("/purchase-tokens", response_model=TransactionResponse)
async def purchase_tokens(
    request: PurchaseTokensRequest,
    current_user=Depends(get_current_user),
    db=Depends(get_db)
):
    """Purchase tokens with real money"""
    # Get package details
    package = await db.fetch_one(
        "SELECT * FROM token_packages WHERE id = :package_id AND is_active = true",
        {"package_id": request.package_id}
    )
    
    if not package:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Token package not found"
        )
    
    # In a real implementation, you would process payment here
    # For now, we'll simulate a successful payment
    
    total_tokens = package["token_amount"] + package["bonus_tokens"]
    
    # Update user balance
    await db.execute(
        "UPDATE users SET tokens = tokens + :tokens WHERE id = :user_id",
        {"tokens": total_tokens, "user_id": current_user["user_id"]}
    )
    
    # Record transaction
    transaction_query = """
    INSERT INTO transactions (user_id, type, token_amount, description, balance_after, created_at)
    VALUES (:user_id, :type, :amount, :description, 
           (SELECT tokens FROM users WHERE id = :user_id), :created_at)
    RETURNING id, user_id, type, amount, description, balance_after, created_at
    """
    
    transaction_data = {
        "user_id": current_user["user_id"],
        "type": "purchase",
        "amount": total_tokens,
        "description": f"Purchased {package['token_amount']} tokens + {package['bonus_tokens']} bonus",
        "created_at": datetime.utcnow()
    }
    
    transaction = await db.fetch_one(transaction_query, transaction_data)
    return TransactionResponse(**dict(transaction))

# Gift management
@router.get("/gifts", response_model=List[GiftItem])
async def get_available_gifts(
    current_user=Depends(get_current_user),
    db=Depends(get_db)
):
    """Get available gifts based on user's trust score"""
    user = await db.fetch_one(
        "SELECT trust_score FROM users WHERE id = :user_id",
        {"user_id": current_user["user_id"]}
    )
    
    query = """
    SELECT * FROM gifts 
    WHERE is_active = true AND trust_score_required <= :trust_score 
    ORDER BY token_cost
    """
    
    gifts = await db.fetch_all(query, {"trust_score": user["trust_score"]})
    return [GiftItem(**dict(gift)) for gift in gifts]


@router.post("/send-gift", response_model=TransactionResponse)
async def send_gift(
    request: SendGiftRequest,
    background_tasks: BackgroundTasks, # Add this
    current_user=Depends(get_current_user),
    db=Depends(get_db)
):
    """Send a gift to another user or a character."""
    
    # --- New logic for character gifts ---
    if isinstance(request.recipient_id, uuid.UUID):
        character_id = request.recipient_id
        if not request.user_prompt:
            raise HTTPException(status_code=400, detail="user_prompt is required for photo generation.")

        # Logic to handle gift for a character (photo generation)
        gift = await db.fetch_one("SELECT * FROM gifts WHERE id = $1 AND is_active = TRUE", request.gift_id)
        if not gift or gift['name'].lower() != 'большой подарок': # Or check by a specific ID
            raise HTTPException(status_code=400, detail="This gift is not valid for a photo request.")

        user = await db.fetch_one("SELECT tokens FROM users WHERE id = $1", current_user["user_id"])
        if user['tokens'] < gift['token_cost']:
            raise HTTPException(status_code=400, detail="Insufficient tokens.")

        await db.execute("UPDATE users SET tokens = tokens - $1 WHERE id = $2", gift['token_cost'], current_user["user_id"])
        
        background_tasks.add_task(
            generate_and_send_photo_task,
            db,
            character_id,
            current_user["user_id"],
            request.user_prompt
        )

        # Create a transaction for the gift purchase
        transaction_query = """
        INSERT INTO transactions (user_id, type, amount, description, balance_after, created_at)
        VALUES ($1, 'gift_sent', $2, $3, (SELECT tokens FROM users WHERE id = $1), NOW())
        RETURNING id, user_id, type, amount, description, balance_after, created_at
        """
        transaction = await db.fetch_row(
            transaction_query,
            current_user["user_id"],
            -gift['token_cost'],
            f"Sent '{gift['name']}' to character {character_id} for a photo."
        )
        return TransactionResponse(**dict(transaction))
    
    # --- Existing logic for user-to-user gifts ---
    # (The original code for sending gifts to other users remains here)
    # ...
    # Check if recipient exists
    recipient = await db.fetch_one(
        "SELECT id FROM users WHERE id = :recipient_id",
        {"recipient_id": request.recipient_id}
    )
    
    if not recipient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Recipient not found"
        )
    
    # Get gift details
    gift = await db.fetch_one(
        "SELECT * FROM gifts WHERE id = :gift_id AND is_active = true",
        {"gift_id": request.gift_id}
    )
    
    if not gift:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Gift not found"
        )
    
    # Check if user has enough tokens
    user = await db.fetch_one(
        "SELECT tokens, trust_score FROM users WHERE id = :user_id",
        {"user_id": current_user["user_id"]}
    )
    
    if user["tokens"] < gift["token_cost"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Insufficient tokens"
        )
    
    if user["trust_score"] < gift["trust_score_required"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient trust score for this gift"
        )
    
    # Deduct tokens from sender
    await db.execute(
        "UPDATE users SET tokens = tokens - :cost WHERE id = :user_id",
        {"cost": gift["token_cost"], "user_id": current_user["user_id"]}
    )
    
    # Add tokens to recipient (or increase trust score)
    if gift["category"] == "premium":
        # Premium gifts increase trust score
        await db.execute(
            "UPDATE users SET trust_score = trust_score + 10 WHERE id = :recipient_id",
            {"recipient_id": request.recipient_id}
        )
    else:
        # Regular gifts add tokens
        await db.execute(
            "UPDATE users SET tokens = tokens + :tokens WHERE id = :recipient_id",
            {"tokens": gift["token_cost"], "recipient_id": request.recipient_id}
        )
    
    # Record gift transaction for sender
    sender_transaction_query = """
    INSERT INTO transactions (user_id, type, amount, description, balance_after, created_at)
    VALUES (:user_id, :type, :amount, :description, 
           (SELECT tokens FROM users WHERE id = :user_id), :created_at)
    RETURNING id, user_id, type, amount, description, balance_after, created_at
    """
    
    sender_transaction_data = {
        "user_id": current_user["user_id"],
        "type": "gift_sent",
        "amount": -gift["token_cost"],
        "description": f"Sent gift '{gift['name']}' to user {request.recipient_id}",
        "created_at": datetime.utcnow()
    }
    
    sender_transaction = await db.fetch_one(sender_transaction_query, sender_transaction_data)
    
    # Record gift transaction for recipient
    recipient_description = f"Received gift '{gift['name']}' from user {current_user['user_id']}"
    if request.message:
        recipient_description += f" with message: {request.message}"
    
    recipient_transaction_data = {
        "user_id": request.recipient_id,
        "type": "gift_received",
        "amount": gift["token_cost"] if gift["category"] != "premium" else 0,
        "description": recipient_description,
        "created_at": datetime.utcnow()
    }
    
    await db.execute(sender_transaction_query, recipient_transaction_data)
    
    return TransactionResponse(**dict(sender_transaction))

# User balance and transaction history
@router.get("/balance", response_model=UserBalanceResponse)
async def get_user_balance(
    current_user=Depends(get_current_user),
    db=Depends(get_db)
):
    """Get current user balance and statistics"""
    user = await db.fetch_one(
        """
        SELECT id, tokens, 
               COALESCE(SUM(CASE WHEN type = 'purchase' THEN amount ELSE 0 END), 0) as total_spent,
               COALESCE(SUM(CASE WHEN type = 'gift_received' THEN amount ELSE 0 END), 0) as total_received
        FROM users 
        LEFT JOIN transactions ON users.id = transactions.user_id
        WHERE users.id = :user_id
        GROUP BY users.id, users.tokens
        """,
        {"user_id": current_user["user_id"]}
    )
    
    return UserBalanceResponse(
        user_id=user["id"],
        balance=user["tokens"],
        total_spent=user["total_spent"],
        total_received=user["total_received"]
    )

@router.get("/transactions", response_model=List[TransactionResponse])
async def get_transaction_history(
    limit: int = 50,
    offset: int = 0,
    current_user=Depends(get_current_user),
    db=Depends(get_db)
):
    """Get user transaction history"""
    query = """
    SELECT * FROM transactions 
    WHERE user_id = :user_id 
    ORDER BY created_at DESC 
    LIMIT :limit OFFSET :offset
    """
    
    transactions = await db.fetch_all(
        query,
        {"user_id": current_user["user_id"], "limit": limit, "offset": offset}
    )
    
    return [TransactionResponse(**dict(tx)) for tx in transactions]