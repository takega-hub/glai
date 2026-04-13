#!/usr/bin/env python3
"""
Completely rebuilds the database by dropping all tables, executing the master schema.sql,
and then applying all subsequent .sql migration files.
"""
import asyncio
import os
from pathlib import Path
import asyncpg

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://glai:opexoboe140546@localhost:5432/eva_ai")
SCHEMA_FILE = Path("/opt/EVA_AI/api/schema.sql")
MIGRATIONS_DIR = Path("/opt/EVA_AI/api/migrations")

async def rebuild_database():
    """Drops, creates, and migrates the database."""
    # Use the Docker-internal hostname if running inside the container context
    db_url = DATABASE_URL
    if os.getenv('DOCKER_ENV'):
        db_url = db_url.replace("localhost", "eva_ai_db")

    print(f"Connecting to {db_url}...")
    conn = await asyncpg.connect(db_url)

    try:
        print("--- Step 1: Dropping all existing public tables ---")
        await conn.execute("""
            DO $$ DECLARE
                r RECORD;
            BEGIN
                FOR r IN (SELECT tablename FROM pg_tables WHERE schemaname = 'public') LOOP
                    EXECUTE 'DROP TABLE IF EXISTS ' || quote_ident(r.tablename) || ' CASCADE';
                END LOOP;
            END $$;
        """)
        print("✓ All public tables dropped.")

        print("--- Step 2: Executing master schema.sql ---")
        if not SCHEMA_FILE.exists():
            print(f"✗ ERROR: Master schema file not found at {SCHEMA_FILE}")
            return
        
        with open(SCHEMA_FILE, 'r') as f:
            schema_sql = f.read()
        await conn.execute(schema_sql)
        print(f"✓ Master schema from {SCHEMA_FILE.name} executed successfully.")

        print("--- Step 3: Applying all .sql migrations ---")
        if not MIGRATIONS_DIR.exists():
            print(f"✗ WARNING: Migrations directory not found at {MIGRATIONS_DIR}")
            return

        sql_files = sorted(list(MIGRATIONS_DIR.glob("*.sql")))
        if not sql_files:
            print("- No .sql migration files found to apply.")
            return

        for sql_file in sql_files:
            try:
                with open(sql_file, 'r') as f:
                    migration_sql = f.read()
                if migration_sql.strip():
                    await conn.execute(migration_sql)
                    print(f"  ✓ Applied migration: {sql_file.name}")
                else:
                    print(f"  - Skipped empty migration: {sql_file.name}")
            except Exception as e:
                print(f"  ✗ Error applying {sql_file.name}: {e}")
        
        print("\n✅ Database rebuild complete!")

    except Exception as e:
        print(f"\nAn unexpected error occurred: {e}")
    finally:
        await conn.close()
        print("Connection closed.")

if __name__ == "__main__":
    # Add a flag to indicate we are in a Docker environment for the script
    os.environ['DOCKER_ENV'] = '1' 
    asyncio.run(rebuild_database())
