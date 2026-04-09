from fastapi import APIRouter, Depends
from api.auth.security import get_current_user
from api.database.connection import get_db

router = APIRouter(prefix="/tokens", tags=["tokens"])

@router.get("/balance")
async def get_token_balance(current_user=Depends(get_current_user), db=Depends(get_db)):
    user_id = current_user['user_id']
    balance = await db.fetchval("SELECT tokens FROM users WHERE id = $1", user_id)
    return {"balance": balance}

@router.get("/history")
async def get_token_history(current_user=Depends(get_current_user), db=Depends(get_db)):
    user_id = current_user['user_id']
    history = await db.fetch("SELECT * FROM transactions WHERE user_id = $1 ORDER BY created_at DESC", user_id)
    return history

@router.get("/packages")
async def get_token_packages(db=Depends(get_db)):
    packages = await db.fetch("SELECT * FROM token_packages WHERE is_active = TRUE ORDER BY price_usd ASC")
    return packages
