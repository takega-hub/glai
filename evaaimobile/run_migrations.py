#!/usr/bin/env python3
"""
Simple migration runner that executes SQL migration files directly.
"""
import asyncio
import os
import sys
from pathlib import Path
import asyncpg

# Database connection from environment
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://glai:opexoboe140546@eva_ai_db:5432/eva_ai")

async def run_migrations():
    """Run all migration files in order."""
    conn = await asyncpg.connect(DATABASE_URL)
    
    try:
        # Get all SQL files from migrations directory
        migrations_dir = Path("/opt/EVA_AI/api/migrations")
        if not migrations_dir.exists():
            print(f"Migrations directory not found: {migrations_dir}")
            return
        
        # Find all .sql files
        sql_files = list(migrations_dir.glob("*.sql"))
        sql_files.sort()  # Sort by filename to ensure consistent order
        
        if not sql_files:
            print("No SQL migration files found")
            return
        
        print(f"Found {len(sql_files)} migration files")
        
        # Execute each migration file
        for sql_file in sql_files:
            print(f"Running migration: {sql_file.name}")
            
            try:
                with open(sql_file, 'r') as f:
                    sql_content = f.read()
                
                if sql_content.strip():
                    await conn.execute(sql_content)
                    print(f"✓ Successfully executed {sql_file.name}")
                else:
                    print(f"- Skipped empty file {sql_file.name}")
                    
            except Exception as e:
                print(f"✗ Error executing {sql_file.name}: {e}")
                # Continue with other migrations even if one fails
        
        print("Migration process completed!")
        
    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(run_migrations())