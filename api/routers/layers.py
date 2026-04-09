from fastapi import APIRouter, Depends, HTTPException, status, File, UploadFile
from pydantic import BaseModel
from typing import Optional, Dict, Any
from api.database.connection import get_db
from api.routers.ai_scenarist import parse_deepseek_response
import uuid
import aiofiles
import os
import httpx
import json

class LayerCreate(BaseModel):
    character_id: uuid.UUID
    name: str = "Новый слой"

class LayerUpdate(BaseModel):
    name: Optional[str] = None
    min_trust_score: Optional[int] = None
    requirements: Optional[Dict[str, Any]] = None
    content_plan: Optional[Dict[str, Any]] = None
    initiator_prompt: Optional[str] = None
    system_prompt_override: Optional[str] = None


UPLOAD_DIRECTORY = "./uploads"

router = APIRouter(
    prefix="/admin/layers",
    tags=["layers_admin"],
)

@router.post("/", summary="Create a new layer for a character")
async def create_layer(layer_data: LayerCreate, db=Depends(get_db)):
    """
    Creates a new layer for a character with default values.
    """
    # Get the highest existing layer_order for the character
    max_order_query = "SELECT MAX(layer_order) FROM layers WHERE character_id = $1"
    max_order = await db.fetchval(max_order_query, layer_data.character_id)
    new_order = (max_order or 0) + 1

    # Get the max_trust from the previous layer to set as the new layer's min_trust
    previous_layer_query = "SELECT max_trust_score FROM layers WHERE character_id = $1 AND layer_order = $2"
    previous_layer = await db.fetchrow(previous_layer_query, layer_data.character_id, new_order - 1)
    min_trust_score = (previous_layer['max_trust_score'] or 0) + 1 if previous_layer else 0

    insert_query = """
        INSERT INTO layers (character_id, name, layer_order, min_trust_score)
        VALUES ($1, $2, $3, $4)
        RETURNING *
    """
    new_layer = await db.fetchrow(
        insert_query, 
        layer_data.character_id, 
        layer_data.name, 
        new_order, 
        min_trust_score
    )
    return new_layer

@router.post("/{layer_id}/upload_photo", summary="Upload photo for a layer")
async def upload_layer_photo(layer_id: uuid.UUID, photo: UploadFile = File(...), db=Depends(get_db)):
    """
    Uploads a photo for a specific layer and updates its media_url.
    """
    # 1. Check if the layer exists and get character_id
    layer = await db.fetchrow("SELECT id, character_id FROM layers WHERE id = $1", layer_id)
    if not layer:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Layer not found")

    character_id = layer['character_id']

    # 2. Create directory
    layer_upload_dir = os.path.join(UPLOAD_DIRECTORY, str(character_id), "layers", str(layer_id))
    os.makedirs(layer_upload_dir, exist_ok=True)

    file_path = os.path.join(layer_upload_dir, photo.filename)

    # 3. Save file
    try:
        async with aiofiles.open(file_path, 'wb') as out_file:
            while content := await photo.read(1024):
                await out_file.write(content)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error saving file: {e}")

    # 4. Update database
    db_file_path = f"/uploads/{character_id}/layers/{layer_id}/{photo.filename}"
    update_query = "UPDATE layers SET media_url = $1 WHERE id = $2"
    await db.execute(update_query, db_file_path, layer_id)

    return {"filePath": db_file_path}

@router.put("/{layer_id}")
async def update_layer(layer_id: int, layer_data: LayerUpdate, db=Depends(get_db)):
    """
    Updates a layer.
    """
    # Fetch the current layer to get all its data
    current_layer = await db.fetchrow("SELECT * FROM layers WHERE id = $1", layer_id)
    if not current_layer:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Layer not found")

    # Create a dictionary from the fetched data
    update_data = dict(current_layer)
    # Update with the new data from the request
    update_data.update(layer_data.dict(exclude_unset=True))

    # The 'requirements' and 'content_plan' fields are JSONB, so they need to be dumped to a JSON string
    if 'requirements' in update_data and isinstance(update_data['requirements'], dict):
        update_data['requirements'] = json.dumps(update_data['requirements'])
    if 'content_plan' in update_data and isinstance(update_data['content_plan'], dict):
        update_data['content_plan'] = json.dumps(update_data['content_plan'])

    # Construct the SET clause for the SQL query
    set_clause = ", ".join([f"{key} = ${i+1}" for i, key in enumerate(update_data.keys())])
    values = list(update_data.values())

    # Add the layer_id for the WHERE clause
    set_clause = set_clause.replace(f"id = ${list(update_data.keys()).index('id')+1}", "") # Don't update the id
    set_clause = set_clause.replace(", ,", ",") # Clean up the set clause
    if set_clause.startswith(", "):
        set_clause = set_clause[2:]
    if set_clause.endswith(", "):
        set_clause = set_clause[:-2]

    update_query = f"""
        UPDATE layers
        SET {set_clause}
        WHERE id = ${len(values)+1}
        RETURNING *
    """
    
    updated_layer = await db.fetchrow(update_query, *values, layer_id)
    
    if not updated_layer:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Layer not found after update")

    return updated_layer



