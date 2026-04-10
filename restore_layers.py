import uuid
import json
import asyncio
import asyncpg
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

async def restore_layers():
    """Restore layers with photo_prompts for existing characters"""
    
    # Sample layer data with photo_prompts
    sample_layers = [
        {
            "character_id": "005ad89a-d71d-4690-a330-20a37153b61d",
            "layer_order": 1,
            "min_trust_score": 0,
            "name": "Layer 1 - Introduction",
            "content_plan": {
                "photo_prompts": [
                    {
                        "id": "550e8400-e29b-41d4-a716-446655440001",
                        "prompt": "A romantic dinner scene with soft lighting",
                        "trust_required": 0,
                        "is_locked": True
                    },
                    {
                        "id": "550e8400-e29b-41d4-a716-446655440002", 
                        "prompt": "A cozy evening at home together",
                        "trust_required": 0,
                        "is_locked": True
                    }
                ]
            }
        },
        {
            "character_id": "005ad89a-d71d-4690-a330-20a37153b61d",
            "layer_order": 2,
            "min_trust_score": 50,
            "name": "Layer 2 - Getting Closer",
            "content_plan": {
                "photo_prompts": [
                    {
                        "id": "550e8400-e29b-41d4-a716-446655440003",
                        "prompt": "A walk in the park holding hands",
                        "trust_required": 50,
                        "is_locked": True
                    }
                ]
            }
        }
    ]
    
    conn = await asyncpg.connect(DATABASE_URL)
    try:
        # Clear existing layers for these characters
        for layer in sample_layers:
            await conn.execute(
                "DELETE FROM layers WHERE character_id = $1",
                uuid.UUID(layer["character_id"])
            )
            
            # Insert new layers
            await conn.execute(
                """INSERT INTO layers (character_id, layer_order, min_trust_score, name, content_plan) 
                   VALUES ($1, $2, $3, $4, $5)""",
                uuid.UUID(layer["character_id"]),
                layer["layer_order"],
                layer["min_trust_score"],
                layer["name"],
                json.dumps(layer["content_plan"])
            )
            print(f"✅ Restored layer {layer['layer_order']} for character {layer['character_id']}")
            
        print("🎉 All layers restored successfully!")
        
        # Verify the restoration
        result = await conn.fetch(
            "SELECT character_id, layer_order, content_plan->'photo_prompts' as photo_prompts FROM layers"
        )
        
        print(f"\n📊 Verification: Found {len(result)} layers")
        for row in result:
            print(f"Character: {row['character_id']}, Layer: {row['layer_order']}, Photos: {len(row['photo_prompts']) if row['photo_prompts'] else 0}")
            
    except Exception as e:
        print(f"❌ Error restoring layers: {e}")
    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(restore_layers())