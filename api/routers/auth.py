from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr
from datetime import datetime
import asyncpg
from api.auth.security import get_password_hash, verify_password, get_current_user
from api.auth.jwt_handler import signJWT
from api.database.connection import get_db

router = APIRouter(prefix="/auth", tags=["authentication"])

import uuid

class UserRegistration(BaseModel):
    username: str
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    id: uuid.UUID
    email: str
    role: str
    created_at: datetime
    tokens: int = 0

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse

@router.post("/register", response_model=TokenResponse)
async def register(user: UserRegistration, db=Depends(get_db)):
    """Register a new user and automatically log them in"""
    # Check if user already exists
    existing_user = await db.fetchrow(
        "SELECT id FROM users WHERE email = $1",
        user.email
    )
    
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Hash password
    hashed_password = get_password_hash(user.password)
    
    # Create user
    query = """
    INSERT INTO users (email, password_hash, role, created_at, tokens)
    VALUES ($1, $2, $3, $4, 100)
    RETURNING id, email, role, created_at, tokens
    """
    
    try:
        new_user = await db.fetchrow(
            query, 
            user.email, hashed_password, 'app_user', datetime.utcnow()
        )
        
        # Generate JWT token for automatic login
        token_data = signJWT(str(new_user['id']), new_user['role'])
        
        return TokenResponse(
            access_token=token_data['access_token'],
            token_type="bearer",
            user=UserResponse(**dict(new_user))
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating user: {str(e)}"
        )

@router.post("/token", response_model=TokenResponse)
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db=Depends(get_db)):
    """Login user and return JWT token"""
    try:
        # Get user from database
        user = await db.fetchrow(
            "SELECT id, email, password_hash, role FROM users WHERE email = $1",
            form_data.username
        )
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )

        password_verified = verify_password(form_data.password, user["password_hash"])

        if not password_verified:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Create JWT token
        token = signJWT(str(user["id"]), user["role"])
        
        # Fetch full user data for response
        user_data = await db.fetchrow(
            "SELECT id, email, role, created_at, tokens FROM users WHERE id = $1",
            user["id"]
        )

        # Convert datetime to string
        user_data_dict = dict(user_data)
        user_data_dict['created_at'] = str(user_data_dict['created_at'])

        return TokenResponse(
            access_token=token["access_token"],
            user=UserResponse(**user_data_dict)
        )
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )

@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user=Depends(get_current_user), db=Depends(get_db)):
    """Get current user information"""
    user = await db.fetchrow(
        "SELECT id, email, role, created_at, tokens, trust_score FROM users WHERE id = $1",
        current_user["user_id"]
    )
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return UserResponse(**dict(user))