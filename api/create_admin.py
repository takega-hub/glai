import asyncio
import asyncpg
import sys
import os
from decouple import config

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api.auth.security import get_password_hash
from datetime import datetime

# Use local .env.local file for localhost connection
DATABASE_URL = config("DATABASE_URL", default="postgresql://postgres:password@localhost:5432/eva_ai")

async def create_admin_user(username, email, password):
    conn = await asyncpg.connect(DATABASE_URL)
    
    # Check if user already exists
    existing_user = await conn.fetchrow(
        "SELECT id FROM users WHERE username = $1 OR email = $2",
        username, email
    )
    
    if existing_user:
        print(f"User {username} or email {email} already exists.")
        await conn.close()
        return

    hashed_password = get_password_hash(password)
    
    query = """
    INSERT INTO users (username, email, password_hash, role, created_at, is_active)
    VALUES ($1, $2, $3, 'super_admin', $4, TRUE)
    """
    
    try:
        await conn.execute(query, username, email, hashed_password, datetime.utcnow())
        print(f"Admin user '{username}' created successfully.")
    except Exception as e:
        print(f"Error creating admin user: {e}")
    finally:
        await conn.close()

if __name__ == "__main__":
    # Replace with your desired credentials
    new_username = "admin"
    new_email = "admin@example.com"
    new_password = "admin123"  # Shorter password to avoid bcrypt length issue
    
    print("Starting admin creation...")
    asyncio.run(create_admin_user(new_username, new_email, new_password))
    print("Admin creation process finished.")
