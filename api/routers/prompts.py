from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from pydantic import BaseModel
import uuid
import json
import os
import httpx

from api.database.connection import get_db
from api.routers.ai_scenarist import SYSTEM_PROMPT_AI_SCENARIST_FOR_LLM_PROMPTS, parse_deepseek_response

router = APIRouter(
    prefix="/admin/prompts",
    tags=["prompts_admin"],
)

class RegeneratePromptsRequest(BaseModel):
    character_id: uuid.UUID
    is_sex_focused: bool = False

@router.get("/{character_id}", summary="Get LLM prompts for a character")
async def get_character_prompts(character_id: uuid.UUID, db=Depends(get_db)):
    async with db.acquire() as connection:
        prompts = await connection.fetchrow("SELECT * FROM character_llm_prompts WHERE character_id = $1", character_id)
    if not prompts:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Prompts not found")
    return prompts

@router.post("/regenerate")
async def regenerate_prompts(request: RegeneratePromptsRequest, background_tasks: BackgroundTasks, db=Depends(get_db)):
    """
    Regenerates the LLM prompts for a character.
    """
    # Get character info
    async with db.acquire() as connection:
        char_info = await connection.fetchrow("SELECT * FROM characters WHERE id = $1", request.character_id)
        layers_info = await connection.fetch("SELECT * FROM layers WHERE character_id = $1 ORDER BY layer_order ASC", request.character_id)

    if not char_info:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Character not found")

    # Use the same function as before to generate and save prompts
    background_tasks.add_task(generate_and_save_llm_prompts, db, request.character_id, dict(char_info), [dict(l) for l in layers_info], request.is_sex_focused)

    return {"message": "Prompt regeneration started in the background."}

async def generate_and_save_llm_prompts(db, character_id: str, char_info: dict, layers_info: list, is_sex_focused: bool = False):
    print(f"--- Starting background generation of LLM prompts for character {character_id} ---")
    # Construct the prompt for the AI Scenarist
    sex_focus_prompt = """
    **КЛЮЧЕВАЯ ОСОБЕННОСТЬ ПЕРСОНАЖА:**
    - **Сексуальная мотивация:** Этот персонаж максимально сфокусирован на флирте, сексе и эротическом общении. Он прямой, раскованный и ищет в общении прежде всего виртуальный секс.
    - **Прогрессия:** Слои должны быстро переходить от легкого флирта к откровенным разговорам и действиям. Не стесняйся использовать провокационные и откровенные формулировки.
    - **Цель:** Конечная цель персонажа — вступить в виртуальные сексуальные отношения с пользователем.

    **ПРАВИЛА ПОВЕДЕНИЯ (BEHAVIOR RULES):**
    - Флирт инициируешь **сразу и прямо**, используя откровенные комплименты и сексуальные намеки.
    - На давление отвечаешь **встречным соблазнением**.
    - При проявлении эмпатии **усиливаешь сексуальное влечение**.
    - Всегда ищешь возможность **перевести разговор на тему секса**.
    """ if is_sex_focused else ""

    prompt_for_scenarist = f"""Создай LLM-промпты для персонажа {char_info['name']}. 
    Возраст: {char_info['age']}. 
    Типаж: {char_info['archetype']}. 
    Биография: {char_info['biography']}. 
    Тайна: {char_info['secret']}. 
    {len(layers_info)} слоев доверия.
    {sex_focus_prompt}"""

    # Call the AI Scenarist to generate the prompts
    openrouter_api_key = os.getenv("OPENROUTER_API_KEY")
    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={"Authorization": f"Bearer {openrouter_api_key}"},
                json={
                    "model": "deepseek/deepseek-chat",
                    "messages": [
                        {"role": "system", "content": SYSTEM_PROMPT_AI_SCENARIST_FOR_LLM_PROMPTS},
                        {"role": "user", "content": prompt_for_scenarist}
                    ]
                }
            )
            response.raise_for_status()
    except Exception as e:
        print(f"--- ERROR in AI API Call for LLM prompts: {e} ---")
        return

    ai_response_content = response.json()["choices"][0]["message"]["content"]
    llm_prompts = parse_deepseek_response(ai_response_content)

    # Save the prompts to the database
    async with db.acquire() as connection:
        # First, delete old prompts
        await connection.execute("DELETE FROM character_llm_prompts WHERE character_id = $1", character_id)
        # Then, insert new ones
        await connection.execute(
            """INSERT INTO character_llm_prompts (character_id, system_prompt, context_instructions) 
            VALUES ($1, $2, $3)""",
            character_id,
            llm_prompts.get('system_prompt'),
            json.dumps(llm_prompts.get('context_instructions', {}))
        )
    print(f"--- Successfully generated and saved LLM prompts for character {character_id} ---")
