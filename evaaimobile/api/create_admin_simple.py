import asyncio
import asyncpg
import sys
import os
from decouple import config

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime

# Use container database connection
DATABASE_URL = config("DATABASE_URL", default="postgresql://postgres:password@db:5432/eva_ai")

import sys
sys.path.append('/opt/EVA_AI')
from api.auth.security import get_password_hash

async def create_admin_user(email, password):
    conn = await asyncpg.connect(DATABASE_URL)
    
    # Check if user already exists
    existing_user = await conn.fetchrow(
        "SELECT id FROM users WHERE email = $1",
        email
    )
    
    if existing_user:
        print(f"User with email {email} already exists.")
        await conn.close()
        return

    hashed_password = get_password_hash(password)
    
    query = """
    INSERT INTO users (email, password_hash, role, created_at, status)
    VALUES ($1, $2, 'super_admin', $3, 'active')
    """
    
    try:
        await conn.execute(query, email, hashed_password, datetime.utcnow())
        print(f"Admin user with email '{email}' created successfully.")
        print(f"Login: {email}")
        print(f"Password: {password}")
    except Exception as e:
        print(f"Error creating admin user: {e}")
    finally:
        await conn.close()

if __name__ == "__main__":
    # Replace with your desired credentials
    new_email = "admin@example.com"
    new_password = "admin123"
    
    print("Starting admin creation...")
    asyncio.run(create_admin_user(new_email, new_password))
    print("Admin creation process finished.")