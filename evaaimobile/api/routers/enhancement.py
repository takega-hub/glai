import json
import httpx
import os

async def _enhance_visual_description_with_scenarist(base_visual_data: dict, character_archetype: str) -> str:
    """Takes basic visual data and uses the Scenarist AI to enhance it into a rich description."""
    print(f"--- Enhancing base visual data with AI Scenarist ---")
    
    base_data_str = json.dumps(base_visual_data)
    
    enhancement_prompt = f"""You are an AI assistant creating a prompt for an image generator. Your task is to expand a basic set of visual data into a detailed, factual physical description. The entire output must be in English.

**BASE DATA (facts from a photo):**
{base_data_str}

**CHARACTER ARCHETYPE:**
{character_archetype}

**YOUR TASK:**
Expand upon the base data to create a detailed physical description in English. You MUST adhere to the facts from the base data (hair color, eye color, etc.). Your goal is to create a list of concrete, descriptive features that can be used to generate a consistent image.

**Example:**
If the base data is `{{"hair_color": "blonde", "eye_color": "blue"}}`, a good enhancement would be:
"oval face, high cheekbones, full lips, perfect makeup, platinum blonde shoulder-length straight hair, blue eyes with a playful sparkle, curvy figure, full bust, thin waist, long legs, height 175cm, a small flower tattoo on her left ankle."

**CRITICAL INSTRUCTIONS:**
- The output MUST be a single line of text in English.
- The output MUST be a comma-separated list of physical attributes.
- DO NOT use artistic or narrative language (e.g., "a vision of allure", "her eyes glittered"). Stick to factual descriptions.
- Describe the face, hair, eyes, body, and add one or two unique features like a tattoo or beauty mark.
"""

    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={"Authorization": f"Bearer {os.getenv('OPENROUTER_API_KEY')}"},
                json={
                    "model": "deepseek/deepseek-chat", 
                    "messages": [{"role": "user", "content": enhancement_prompt}]
                }
            )
            response.raise_for_status()
            enhanced_description = response.json()['choices'][0]['message']['content'].strip()
            print(f"--- AI Scenarist enhanced description: {enhanced_description} ---")
            return enhanced_description
    except Exception as e:
        print(f"!!! FAILED to enhance visual description: {e} !!!")
        # Fallback to a simple description based on the initial data
        hair = base_visual_data.get('hair_color', 'hair')
        eyes = base_visual_data.get('eye_color', 'eyes')
        body = base_visual_data.get('body_type', 'body')
        return f"A beautiful woman with {hair}, {eyes}, and a {body}."

