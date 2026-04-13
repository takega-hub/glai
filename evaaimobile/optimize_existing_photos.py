import os
import asyncio
import asyncpg
from dotenv import load_dotenv

# Explicitly load the .env file from the api directory
load_dotenv(dotenv_path="/opt/EVA_AI/api/.env")
from api.services.image_optimizer import ImageOptimizerService

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
UPLOADS_DIR = "/opt/EVA_AI/uploads"

async def update_media_url_in_db(connection, old_path: str, new_path: str):
    """Updates the media_url in both the content and layers tables."""
    print(f"--- DB UPDATE: {old_path} -> {new_path} ---")
    # Update in content table (for teasers)
    await connection.execute("UPDATE content SET media_url = $1 WHERE media_url = $2", new_path, old_path)

    # Update in layers table (for layer content)
    # This is more complex as the URL is inside a JSONB field.
    # We need to fetch, modify, and then update.
    layers_to_update = await connection.fetch("SELECT id, content_plan FROM layers WHERE content_plan::text LIKE $1", f'%{old_path}%')
    for layer in layers_to_update:
        content_plan_str = layer['content_plan']
        try:
            content_plan = json.loads(content_plan_str) if isinstance(content_plan_str, str) else content_plan_str
        except (json.JSONDecodeError, TypeError):
            print(f"--- DB UPDATE: Skipping layer {layer['id']} due to malformed JSON ---")
            continue

        updated = False
        for content_type in ['photo_prompts', 'video_prompts']:
            if content_type in content_plan and content_plan[content_type]:
                # Handle both list and dict structures
                prompts = content_plan[content_type]
                prompt_list = []
                if isinstance(prompts, dict):
                    prompt_list = prompts.values()
                elif isinstance(prompts, list):
                    prompt_list = prompts

                for item in prompt_list:
                    if isinstance(item, dict) and item.get('media_url') == old_path:
                        item['media_url'] = new_path
                        updated = True
        if updated:
            await connection.execute("UPDATE layers SET content_plan = $1 WHERE id = $2", json.dumps(content_plan), layer['id'])
            print(f"--- DB UPDATE: Updated layer {layer['id']} ---")

async def main():
    optimizer = ImageOptimizerService()
    db_pool = await asyncpg.create_pool(DATABASE_URL)
    
    async with db_pool.acquire() as connection:
        for root, _, files in os.walk(UPLOADS_DIR):
            for file in files:
                if file.lower().endswith(('.png', '.jpeg', '.webp')):
                    original_path = os.path.join(root, file)
                    db_path = "/" + os.path.relpath(original_path, "/opt/EVA_AI")
                    new_db_path = "/" + os.path.relpath(os.path.splitext(original_path)[0] + ".jpg", "/opt/EVA_AI")

                    print(f"Processing: {original_path}")
                    try:
                        with open(original_path, 'rb') as f:
                            image_bytes = f.read()
                        
                        optimized_bytes = optimizer.optimize_image(image_bytes)
                        
                        # Create new file path
                        new_path = os.path.splitext(original_path)[0] + ".jpg"
                        
                        # Save new file
                        with open(new_path, 'wb') as f:
                            f.write(optimized_bytes)
                        print(f"   -> Saved optimized file to {new_path}")

                        # Update database
                        await update_media_url_in_db(connection, db_path, new_db_path)

                        # Delete original if it's not the same file
                        if original_path != new_path:
                            os.remove(original_path)
                            print(f"   -> Deleted original file: {original_path}")

                    except Exception as e:
                        print(f"!!! ERROR processing {original_path}: {e} !!!")
    
    await db_pool.close()
    print("\n--- Optimization Complete ---")

if __name__ == "__main__":
    asyncio.run(main())
