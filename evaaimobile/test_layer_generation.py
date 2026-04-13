import httpx
import asyncio

async def main():
    character_id = "005ad89a-d71d-4690-a330-20a37153b61d"
    url = f"http://localhost:8087/admin/characters/{character_id}/generate-layers-content"
    # This is a sample layer. In a real scenario, you would fetch this from the database.
    layers = [
        {
            "id": "c9b8f8f0-1b1a-4b0e-9b0a-0e1b0e1b0e1b", # This should be the actual layer ID
            "layer_order": 1,
            "emotional_state": "curious",
            "what_is_revealed": "a small secret"
        }
    ]
    data = {
        "sexuality_level": 1,
        "layers": layers
    }
    
    try:
        async with httpx.AsyncClient(timeout=300.0) as client:
            # You need to replace this with a valid admin token
            headers = {"Authorization": "Bearer your_admin_token"}
            response = await client.post(url, json=data, headers=headers)
            response.raise_for_status()
            print("Successfully triggered layer content generation.")
            print(response.json())
    except httpx.HTTPStatusError as e:
        print(f"Error generating layer content: {e.response.status_code}")
        print(e.response.text)
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    asyncio.run(main())