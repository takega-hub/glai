import asyncio
import asyncpg
import sys
import os
from decouple import config

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api.auth.security import get_password_hash
from datetime import datetime

# Connect to localhost since we are running from the host
DATABASE_URL = config("DATABASE_URL", default="postgresql://postgres:password@localhost:5432/eva_ai")

async def create_correct_admin():
    conn = None
    try:
        print("Connecting to the database...")
        conn = await asyncpg.connect(DATABASE_URL)
        print("Database connection successful.")
        
        email = "admin@example.com"
        password = "admin123"
        
        print(f"Hashing password for {email}...")
        hashed_password = get_password_hash(password)
        print("Password hashed successfully.")
        
        query = """
        INSERT INTO users (email, password_hash, role, created_at, status)
        VALUES ($1, $2, 'super_admin', $3, 'active')
        """
        
        print("Executing INSERT query...")
        await conn.execute(query, email, hashed_password, datetime.utcnow())
        print(f"Correct admin user with email '{email}' created successfully.")

    except Exception as e:
        print(f"Error creating correct admin user: {e}")
    finally:
        if conn:
            print("Closing database connection.")
            await conn.close()

if __name__ == "__main__":
    print("Starting correct admin creation...")
    asyncio.run(create_correct_admin())
    print("Correct admin creation process finished.")
