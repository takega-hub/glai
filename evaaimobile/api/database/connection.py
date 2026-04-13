import asyncpg
from decouple import config

DATABASE_URL = config("DATABASE_URL")

pool = None

async def connect_to_db():
    global pool
    pool = await asyncpg.create_pool(DATABASE_URL)

async def close_db_connection():
    await pool.close()

async def get_db():
    if pool is None:
        await connect_to_db()
    yield pool

async def run_migrations(pool):
    print("Running DB migrations...")
    async with pool.acquire() as connection:
        # Check if layer_id column exists
        column_exists = await connection.fetchval("""
            SELECT EXISTS (
                SELECT 1
                FROM information_schema.columns 
                WHERE table_name='content' AND column_name='layer_id'
            );
        """)

        if not column_exists:
            print("Adding 'layer_id' column to 'content' table...")
            await connection.execute("ALTER TABLE content ADD COLUMN layer_id INTEGER;")
            print("Column 'layer_id' added.")
        else:
            print("Column 'layer_id' already exists.")