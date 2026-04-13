import asyncpg
import asyncio

async def test_connection():
    # Test different connection URLs
    urls = [
        'postgresql://postgres:password@localhost:5432/eva_ai',
        'postgresql://postgres:password@127.0.0.1:5432/eva_ai',
        'postgresql://postgres:password@host.docker.internal:5432/eva_ai',
        'postgresql://postgres:password@172.19.0.2:5432/eva_ai',
    ]
    
    for url in urls:
        print(f"Testing: {url}")
        try:
            conn = await asyncpg.connect(url)
            print(f"✅ SUCCESS with {url}")
            result = await conn.fetchval('SELECT 1')
            print(f"Test query result: {result}")
            await conn.close()
            return
        except Exception as e:
            print(f"❌ FAILED with {url}: {e}")
        print()

if __name__ == "__main__":
    asyncio.run(test_connection())