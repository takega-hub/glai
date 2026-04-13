#!/usr/bin/env python3
"""
Creates the default admin user.
"""
import asyncio
import os
import asyncpg
from api.auth.security import get_password_hash # Assuming this path is correct

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://glai:opexoboe140546@localhost:5432/eva_ai")

async def create_admin_user():
    """Creates the default admin user if it doesn't exist."""
    db_url = DATABASE_URL
    if os.getenv('DOCKER_ENV'):
        db_url = db_url.replace("localhost", "eva_ai_db")

    print(f"Connecting to {db_url}...")
    conn = await asyncpg.connect(db_url)

    try:
        print("--- Creating default admin user ---")
        
        # Hash the password
        admin_password_hash = get_password_hash("admin123")
        
        # Insert the admin user
        await conn.execute("""
            INSERT INTO users (email, password_hash, role)
            VALUES ($1, $2, 'super_admin')
            ON CONFLICT (email) DO NOTHING;
        """, 'admin@example.com', admin_password_hash)
        
        print("✓ Default admin user 'admin@example.com' created or already exists.")

    except Exception as e:
        print(f"\nAn unexpected error occurred: {e}")
    finally:
        await conn.close()
        print("Connection closed.")

if __name__ == "__main__":
    os.environ['DOCKER_ENV'] = '1'
    # We need to make sure the script can find the 'api' module
    import sys
    sys.path.append('/opt/EVA_AI')
    asyncio.run(create_admin_user())
