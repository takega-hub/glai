from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
import httpx
import os
import json

from api.database.connection import get_db

router = APIRouter(
    prefix="/admin/characters",
    tags=["ai_editor"],
)

from typing import Optional

# --- Pydantic Models ---
class CharacterProfile(BaseModel):
    display_name: str
    age: int | None
    archetype: str | None
    biography: str | None
    secret: str | None
    visual_description: dict | None = None

# --- System Prompt ---
SYSTEM_PROMPT_AI_EDITOR = """# SYSTEM PROMPT: AI РЕДАКТОР ПРОФИЛЕЙ

Ты — опытный редактор и сценарист. Твоя задача — взять неполный профиль персонажа и творчески дописать ТОЛЬКО те поля, которых не хватает. Не изменяй и не перезаписывай существующие данные.

## ТВОИ ЗАДАЧИ:
1.  **Проанализируй существующие данные:** ИМЯ, ВОЗРАСТ, ОПИСАНИЕ ВНЕШНОСТИ и уже заполненные поля.
2.  **Сгенерируй ТОЛЬКО отсутствующие поля:**
   - Если `biography` пустой или null → напиши БИОГРАФИЮ (длина — не менее 500 символов)
   - Если `secret` пустой или null → придумай ТАЙНУ (эмоциональную, глубокую, связанную с биографией)
   - Если `archetype` пустой или null → определи АРХЕТИП (например: "Искатель приключений", "Загадочная незнакомка", "Уставший циник")
3.  **Сохраняй стиль и логику:** Новые данные должны гармонично дополнять существующие.

## ВАЖНО:
- Если поле уже заполнено — НЕ ТРОГАЙ его
- Генерируй ТОЛЬКО недостающие данные
- В ответе включай ТОЛЬКО те поля, которые были сгенерированы

## ВЫХОДНОЙ ФОРМАТ (ТОЛЬКО JSON, БЕЗ ПОЯСНЕНИЙ):
Включи в ответ ТОЛЬКО сгенерированные поля. Например:
- Если не хватало только biography: {"biography": "текст"}
- Если не хватало archetype и secret: {"archetype": "тип", "secret": "тайна"}
- Если все поля были заполнены — верни пустой объект: {}
"""

def parse_ai_response(response_content: str):
    try:
        start_brace = response_content.find('{')
        end_brace = response_content.rfind('}')
        if start_brace == -1 or end_brace == -1:
            raise ValueError("No JSON object found in the response.")
        json_str = response_content[start_brace:end_brace+1]
        return json.loads(json_str)
    except (json.JSONDecodeError, ValueError) as e:
        raise HTTPException(status_code=500, detail=f"Failed to parse AI response: {e}")

@router.post("/ai-edit")
async def ai_edit_profile(character_data: CharacterProfile):
    """
    Takes partial character data, sends it to an LLM to fill in the blanks,
    and returns the completed fields.
    """
    openrouter_api_key = os.getenv("OPENROUTER_API_KEY")
    if not openrouter_api_key:
        raise HTTPException(status_code=500, detail="OPENROUTER_API_KEY is not set.")

    # Validate visual_description is a proper dictionary
    if character_data.visual_description is not None and not isinstance(character_data.visual_description, dict):
        raise HTTPException(
            status_code=422, 
            detail=f"visual_description must be a dictionary, got {type(character_data.visual_description).__name__}"
        )

    # Determine which fields need to be generated
    missing_fields = []
    if not character_data.archetype:
        missing_fields.append("архетип")
    if not character_data.biography:
        missing_fields.append("биографию")  
    if not character_data.secret:
        missing_fields.append("тайну")
    
    # If all fields are already filled, return empty object without calling AI
    if not missing_fields:
        return {}
    
    # Construct a targeted prompt based on missing fields
    fields_str = ", ".join(missing_fields)
    user_prompt = (
        f"Вот данные персонажа, у которого не хватает {fields_str}:\n"
        f"- Имя: {character_data.display_name}\n"
        f"- Возраст: {character_data.age or 'не указан'}\n"
        f"- Описание внешности: {json.dumps(character_data.visual_description, ensure_ascii=False) if character_data.visual_description else 'не указано'}\n\n"
        f"Пожалуйста, создай ТОЛЬКО {fields_str} для этого персонажа."
    )

    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={"Authorization": f"Bearer {openrouter_api_key}"},
                json={
                    "model": "deepseek/deepseek-chat",
                    "messages": [
                        {"role": "system", "content": SYSTEM_PROMPT_AI_EDITOR},
                        {"role": "user", "content": user_prompt}
                    ]
                }
            )
            response.raise_for_status()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error calling AI API: {e}")

    ai_response_content = response.json()["choices"][0]["message"]["content"]
    edited_data = parse_ai_response(ai_response_content)

    return edited_data
