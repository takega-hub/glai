from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional
from pydantic import BaseModel, EmailStr, Field
from datetime import datetime
import uuid

from api.auth.security import role_required, roles_required
from api.database.connection import get_db

router = APIRouter(prefix="/admin", tags=["admin"])

class UserOut(BaseModel):
    id: uuid.UUID
    email: EmailStr
    display_name: Optional[str]
    role: str
    status: str
    created_at: datetime
    last_active_at: Optional[datetime]

class UsersResponse(BaseModel):
    total: int
    users: List[UserOut]

class UserCreate(BaseModel):
    email: EmailStr
    display_name: Optional[str] = None
    password: str = Field(..., min_length=6)
    role: str = Field(default="app_user", pattern="^(app_user|admin|super_admin)$")

class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    display_name: Optional[str] = None
    role: Optional[str] = Field(None, pattern="^(app_user|admin|super_admin)$")
    status: Optional[str] = Field(None, pattern="^(active|blocked)$")
    add_tokens: Optional[int] = Field(None, ge=0)

class PasswordChange(BaseModel):
    current_password: str
    new_password: str = Field(..., min_length=6)
    confirm_password: str

class UserDetail(BaseModel):
    id: uuid.UUID
    email: EmailStr
    display_name: Optional[str]
    role: str
    status: str
    created_at: datetime
    last_active_at: Optional[datetime]
    tokens_balance: int = 0

@router.get("/users", response_model=UsersResponse)
async def get_users(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    search: Optional[str] = Query(None),
    db=Depends(get_db),
    current_user=Depends(roles_required(['admin', 'super_admin']))
):
    """Get a list of users with pagination and search."""
    offset = (page - 1) * limit

    base_query = "FROM users WHERE role = 'app_user'"
    count_query = "SELECT COUNT(*) " + base_query
    data_query = "SELECT u.id, u.email, up.display_name, u.role, u.status, u.created_at, u.last_active_at FROM users u LEFT JOIN user_profiles up ON u.id = up.user_id WHERE u.role = 'app_user'"

    params = {}
    if search:
        search_filter = " AND (email ILIKE $1 OR display_name ILIKE $1)"
        count_query += search_filter
        data_query += search_filter
        params["1"] = f"%{search}%"

    total = await db.fetchval(count_query, *params.values())

    data_query += f" ORDER BY created_at DESC LIMIT ${len(params) + 1} OFFSET ${len(params) + 2}"
    
    users = await db.fetch(data_query, *params.values(), limit, offset)

    return UsersResponse(total=total, users=[UserOut(**user) for user in users])

@router.get("/users/{user_id}", response_model=UserDetail)
async def get_user(
    user_id: uuid.UUID,
    db=Depends(get_db),
    current_user=Depends(roles_required(['admin', 'super_admin']))
):
    """Get detailed information about a specific user."""
    user = await db.fetchrow(
        """SELECT u.id, u.email, up.display_name, u.role, u.status, u.created_at, u.last_active_at, u.tokens as tokens_balance
           FROM users u
           LEFT JOIN user_profiles up ON u.id = up.user_id
           WHERE u.id = $1""",
        user_id
    )
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return UserDetail(**user)

@router.post("/users", response_model=UserDetail)
async def create_user(
    user_data: UserCreate,
    db=Depends(get_db),
    current_user=Depends(roles_required(['super_admin']))
):
    """Create a new user. Only super admins can create users."""
    # Check if email already exists
    existing_user = await db.fetchrow("SELECT id FROM users WHERE email = $1", user_data.email)
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    from api.auth.security import get_password_hash
    
    user = await db.fetchrow(
        """INSERT INTO users (email, password_hash, display_name, role, created_at, last_active, status)
           VALUES ($1, $2, $3, $4, NOW(), NOW(), 'active') RETURNING *""",
        user_data.email,
        get_password_hash(user_data.password),
        user_data.display_name,
        user_data.role
    )
    
    return UserDetail(**user, tokens_balance=0)

@router.put("/users/{user_id}", response_model=UserDetail)
async def update_user(
    user_id: uuid.UUID,
    user_data: UserUpdate,
    db=Depends(get_db),
    current_user=Depends(roles_required(['admin', 'super_admin']))
):
    """Update user information."""
    # Check if user exists
    existing_user = await db.fetchrow("SELECT id FROM users WHERE id = $1", user_id)
    if not existing_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Check if email is being changed and if it's already taken
    if user_data.email:
        email_taken = await db.fetchrow(
            "SELECT id FROM users WHERE email = $1 AND id != $2",
            user_data.email, user_id
        )
        if email_taken:
            raise HTTPException(status_code=400, detail="Email already in use")
    
    # Build dynamic update query
    update_fields = []
    params = []
    param_count = 1
    
    if user_data.email is not None:
        update_fields.append(f"email = ${param_count}")
        params.append(user_data.email)
        param_count += 1
    
    if user_data.display_name is not None:
        update_fields.append(f"display_name = ${param_count}")
        params.append(user_data.display_name)
        param_count += 1
    
    if user_data.role is not None:
        update_fields.append(f"role = ${param_count}")
        params.append(user_data.role)
        param_count += 1
    
    if user_data.status is not None:
        update_fields.append(f"status = ${param_count}")
        params.append(user_data.status)
        param_count += 1
    
    if not update_fields and user_data.add_tokens is None:
        raise HTTPException(status_code=400, detail="No fields to update")
    
    params.append(user_id)
    
    user = await db.fetchrow(
        f"UPDATE users SET {', '.join(update_fields)} WHERE id = ${param_count} RETURNING *",
        *params
    )
    
    if user_data.add_tokens is not None and user_data.add_tokens > 0:
        await db.execute(
            "UPDATE users SET tokens = tokens + $1 WHERE id = $2",
            user_data.add_tokens, user_id
        )
        # Create a transaction record for the token addition
        await db.execute(
            """INSERT INTO transactions (user_id, type, token_amount, status, description) 
               VALUES ($1, 'admin_grant', $2, 'completed', 'Tokens granted by administrator')""",
            user_id, user_data.add_tokens
        )

    # Get tokens balance
    tokens_balance = await db.fetchval(
        "SELECT COALESCE(SUM(tokens_balance), 0) FROM user_character_state WHERE user_id = $1",
        user_id
    ) or 0
    
    return UserDetail(**user, tokens_balance=tokens_balance)

@router.delete("/users/{user_id}")
async def delete_user(
    user_id: uuid.UUID,
    db=Depends(get_db),
    current_user=Depends(roles_required(['super_admin']))
):
    """Delete a user. Only super admins can delete users."""
    # Check if user exists
    existing_user = await db.fetchrow("SELECT id FROM users WHERE id = $1", user_id)
    if not existing_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Check if user is trying to delete themselves
    if str(user_id) == str(current_user['user_id']):
        raise HTTPException(status_code=400, detail="Cannot delete your own account")
    
    # Delete user (cascade will handle related data)
    await db.execute("DELETE FROM users WHERE id = $1", user_id)
    
    return {"message": "User deleted successfully"}

@router.put("/settings/password")
async def change_admin_password(
    password_data: PasswordChange,
    db=Depends(get_db),
    current_user=Depends(roles_required(['admin', 'super_admin']))
):
    """Change the password for the current admin user."""
    if password_data.new_password != password_data.confirm_password:
        raise HTTPException(
            status_code=400,
            detail="New password and confirmation do not match"
        )

    user_id = uuid.UUID(current_user['user_id'])
    user = await db.fetchrow("SELECT password_hash FROM users WHERE id = $1", user_id)

    if not user:
        raise HTTPException(status_code=404, detail="Admin user not found")

    from api.auth.security import verify_password, get_password_hash

    if not verify_password(password_data.current_password, user['password_hash']):
        raise HTTPException(status_code=400, detail="Incorrect current password")

    new_hashed_password = get_password_hash(password_data.new_password)
    await db.execute(
        "UPDATE users SET password_hash = $1 WHERE id = $2",
        new_hashed_password, user_id
    )

    return {"message": "Password updated successfully"}

# Export the router
__all__ = ["router"]

