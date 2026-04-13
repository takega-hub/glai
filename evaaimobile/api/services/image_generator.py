import httpx
import base64
import json
import os
import aiofiles

class OpenRouterImageGenerator:
    def __init__(self, api_key: str):
        if not api_key:
            raise ValueError("OpenRouter API key is required.")
        self.api_key = api_key
        self.base_url = "https://openrouter.ai/api/v1"
        self.text_to_image_models = [
            "bytedance-seed/seedream-4.5",      # Primary
            "sourceful/riverflow-v2-fast",      # Fallback 1
                      
        ]

    async def _save_image(self, image_bytes: bytes, folder_path: str, file_name: str) -> str:
        """Saves image bytes to a file and returns the database-ready path."""
        os.makedirs(folder_path, exist_ok=True)
        full_path = os.path.join(folder_path, file_name)
        
        async with aiofiles.open(full_path, 'wb') as f:
            await f.write(image_bytes)
            
        # Return a path that can be served, assuming 'uploads' is a static directory
        db_path = os.path.join("/uploads", os.path.relpath(full_path, "uploads"))
        return db_path.replace("\\", "/")

    async def generate_from_text(self, prompt: str) -> bytes:
        """Generates an image from a text prompt using the chat/completions endpoint with modalities."""
        model_to_use = "google/gemini-3.1-flash-image-preview"
        print(f"--- Attempting to generate image with model: {model_to_use} using /chat/completions ---")

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        # Correct payload structure for text-to-image with modalities
        payload = {
            "model": model_to_use,
            "modalities": ["image"], # This is the key parameter
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        }

        try:
            async with httpx.AsyncClient(timeout=180.0) as client:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers=headers,
                    json=payload
                )
                response.raise_for_status()
                data = response.json()

                if "choices" in data and len(data["choices"]) > 0:
                    message = data["choices"][0].get("message", {})
                    # As per the user's example, check the 'images' field first
                    if "images" in message and len(message["images"]) > 0:
                        image_info = message["images"][0]
                        image_url = image_info.get("image_url", {}).get("url")
                        if image_url and image_url.startswith("data:image"):
                            b64_json = image_url.split(",", 1)[1]
                            print(f"--- Successfully generated image with {model_to_use} from 'images' field ---")
                            return base64.b64decode(b64_json)

            raise Exception("No valid image data found in the response.")

        except httpx.HTTPStatusError as e:
            print(f"HTTP error during image generation: {e.response.status_code} - {e.response.text}")
            print(f"Request payload: {json.dumps(payload, indent=2, ensure_ascii=False)}")
            raise
        except Exception as e:
            print(f"An error occurred during image generation: {e}")
            raise

    async def generate_with_reference(self, model: str, reference_photo_path: str, prompt: str) -> bytes:
        """
        Generates an image using a unified endpoint for all specified models.
        """
        with open(reference_photo_path, "rb") as f:
            ref_b64 = base64.b64encode(f.read()).decode()

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        # System prompt for better results
        system_prompt = "You are a professional image generator. Create high-quality, photorealistic images based on the user's instructions."

        payload = {
            "model": model,
            "modalities": ["image"],
            "messages": [
                {
                    "role": "system",
                    "content": system_prompt
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": f"Create an image of the SAME PERSON as in the reference. Face must be identical. {prompt}"
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{ref_b64}"
                            }
                        }
                    ]
                }
            ],
            "max_tokens": 1500,
            "image_config": {
                "aspect_ratio": "1:1",
                "image_size": "1K"
            }
        }
        
        print(f"--- Sending Unified Generation Request ---")
        print(f"Model: {model}")
        print(f"Modalities: [\"image\"]")
        print(f"Prompt: {prompt}")
        print(f"Reference photo path: {reference_photo_path}")
        print(f"Full payload structure (simplified): {json.dumps({'model': model, 'modalities': ['image'], 'messages': ['system', 'user']}, indent=2)}")

        try:
            async with httpx.AsyncClient(timeout=180.0) as client:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers=headers,
                    json=payload
                )
                response.raise_for_status()
                data = response.json()

                print(f"--- Received Unified Generation Response ---\n{json.dumps(data, indent=2, ensure_ascii=False)}")

                # --- Robust Unified Response Parser ---
                if "choices" in data and len(data["choices"]) > 0:
                    message = data["choices"][0].get("message", {})

                    # Attempt 1: Check `message.content` (standard for Gemini, etc.)
                    if "content" in message and isinstance(message["content"], list):
                        for part in message["content"]:
                            if isinstance(part, dict) and part.get("type") == "image_url":
                                image_url = part.get("image_url", {}).get("url")
                                if image_url and "," in image_url:
                                    img_b64 = image_url.split(",")[1]
                                    print("--- Image found in 'content' field ---")
                                    return base64.b64decode(img_b64)
                    
                    # Attempt 2: Check `message.images` (alternative format seen in logs)
                    if "images" in message and isinstance(message["images"], list) and len(message["images"]) > 0:
                        image_info = message["images"][0]
                        if "image_url" in image_info and "url" in image_info["image_url"]:
                            image_url = image_info["image_url"]["url"]
                            if image_url and "," in image_url:
                                img_b64 = image_url.split(",")[1]
                                print("--- Image found in 'images' field ---")
                                return base64.b64decode(img_b64)

                raise Exception("No image found in any known location in the response.")

        except httpx.HTTPStatusError as e:
            print(f"HTTP error occurred: {e.response.status_code} - {e.response.text}")
            print(f"Request payload: {json.dumps(payload, indent=2, ensure_ascii=False)}")
            raise
        except Exception as e:
            print(f"An error occurred: {e}")
            raise
