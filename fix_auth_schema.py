#!/usr/bin/env python3
"""
Fix authentication schema to match application expectations.
"""
import asyncio
import os
import asyncpg

# Database connection from environment
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://glai:opexoboe140546@eva_ai_db:5432/eva_ai")

async def fix_auth_schema():
    """Fix the users table to match application expectations."""
    conn = await asyncpg.connect(DATABASE_URL)
    
    try:
        print("Fixing authentication schema...")
        
        # Step 1: Add missing columns to users table
        await conn.execute("""
            ALTER TABLE users 
            ADD COLUMN IF NOT EXISTS email VARCHAR(255) UNIQUE,
            ADD COLUMN IF NOT EXISTS password_hash VARCHAR(255),
            ADD COLUMN IF NOT EXISTS role VARCHAR(50) DEFAULT 'app_user',
            ADD COLUMN IF NOT EXISTS trust_score INTEGER DEFAULT 0;
        """)
        print("✓ Added email, password_hash, role, trust_score columns")
        
        # Step 2: Create a new users table with UUID primary key
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS users_new (
                id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
                email VARCHAR(255) UNIQUE NOT NULL,
                password_hash VARCHAR(255) NOT NULL,
                username VARCHAR(255),
                telegram_id BIGINT UNIQUE,
                first_name VARCHAR(255),
                last_name VARCHAR(255),
                language_code VARCHAR(10),
                is_premium BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_active BOOLEAN DEFAULT TRUE,
                tokens INTEGER DEFAULT 0,
                subscription_status VARCHAR(50) DEFAULT 'free',
                subscription_end_date TIMESTAMP,
                avatar_url VARCHAR(500),
                display_name VARCHAR(255),
                last_active TIMESTAMP,
                role VARCHAR(50) DEFAULT 'app_user',
                trust_score INTEGER DEFAULT 0
            );
        """)
        print("✓ Created new users table with UUID primary key")
        
        # Step 3: Copy existing data to new table (if any)
        await conn.execute("""
            INSERT INTO users_new (
                username, telegram_id, first_name, last_name, language_code,
                is_premium, created_at, updated_at, last_activity, is_active,
                tokens, subscription_status, subscription_end_date, avatar_url,
                display_name, last_active
            )
            SELECT 
                username, telegram_id, first_name, last_name, language_code,
                is_premium, created_at, updated_at, last_activity, is_active,
                tokens, subscription_status, subscription_end_date, avatar_url,
                display_name, last_active
            FROM users
            WHERE telegram_id IS NOT NULL;
        """)
        print("✓ Copied existing Telegram user data to new table")
        
        # Step 4: Drop foreign key constraints first
        await conn.execute("ALTER TABLE user_character_state DROP CONSTRAINT IF EXISTS user_character_state_user_id_fkey;")
        await conn.execute("ALTER TABLE transactions DROP CONSTRAINT IF EXISTS transactions_user_id_fkey;")
        print("✓ Dropped foreign key constraints")
        
        # Step 5: Drop old table and rename new table
        await conn.execute("DROP TABLE IF EXISTS users;")
        await conn.execute("ALTER TABLE users_new RENAME TO users;")
        print("✓ Replaced old users table with new UUID-based table")
        
        # Step 6: Recreate foreign key constraints with UUID references
        await conn.execute("""
            ALTER TABLE user_character_state 
            ADD CONSTRAINT user_character_state_user_id_fkey 
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE;
        """)
        await conn.execute("""
            ALTER TABLE transactions 
            ADD CONSTRAINT transactions_user_id_fkey 
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE;
        """)
        print("✓ Recreated foreign key constraints with UUID references")
        
        # Step 7: Create indexes for better performance
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);")
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_users_telegram_id ON users(telegram_id);")
        print("✓ Created indexes")
        
        # Step 8: Create a default admin user for testing
        from api.auth.security import get_password_hash
        admin_password_hash = get_password_hash("admin123")
        
        await conn.execute("""
            INSERT INTO users (email, password_hash, username, role, tokens, is_active)
            VALUES ('admin@example.com', $1, 'admin', 'admin', 1000, true)
            ON CONFLICT (email) DO NOTHING;
        """, admin_password_hash)
        print("✓ Created default admin user (admin@example.com / admin123)")
        
        print("\n✅ Authentication schema fixed successfully!")
        
        # Show final table structure
        columns = await conn.fetch("""
            SELECT column_name, data_type, is_nullable, column_default
            FROM information_schema.columns 
            WHERE table_name = 'users' 
            ORDER BY ordinal_position;
        """)
        
        print("\nFinal users table structure:")
        for col in columns:
            print(f"  - {col['column_name']}: {col['data_type']} {col['is_nullable']} {col['column_default'] or ''}")
        
    except Exception as e:
        print(f"Error fixing auth schema: {e}")
        raise
    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(fix_auth_schema())