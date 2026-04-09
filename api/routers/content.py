from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from pydantic import BaseModel
import uuid
import json
import os
import aiofiles

from api.database.connection import get_db

router = APIRouter(
    prefix="/admin/content",
    tags=["content_admin"],
)

@router.post("/{content_item_id}/upload")
async def upload_content(content_item_id: str, file: UploadFile = File(...), db=Depends(get_db)):
    """
    Uploads a media file for a specific content item and updates the media_url.
    """
    # Find the layer containing the content item
    query = """
        SELECT l.id, l.content_plan, l.character_id
        FROM layers l, jsonb_array_elements(l.content_plan->'photo_prompts') as item
        WHERE item->>'id' = $1
        UNION
        SELECT l.id, l.content_plan, l.character_id
        FROM layers l, jsonb_array_elements(l.content_plan->'video_prompts') as item
        WHERE item->>'id' = $1
        UNION
        SELECT l.id, l.content_plan, l.character_id
        FROM layers l, jsonb_array_elements(l.content_plan->'audio_texts') as item
        WHERE item->>'id' = $1
    """
    layer = await db.fetchrow(query, content_item_id)

    # If not found in layers, check the teaser content
    if not layer:
        teaser_query = "SELECT id, character_id FROM content WHERE id = $1 AND subtype = 'teaser'"
        teaser_item = await db.fetchrow(teaser_query, content_item_id)
        if teaser_item:
            # Handle teaser upload
            upload_dir = os.path.join("uploads", str(teaser_item['character_id']), "content")
            os.makedirs(upload_dir, exist_ok=True)
            file_extension = file.filename.split('.')[-1]
            unique_filename = f"{content_item_id}.{file_extension}"
            file_path = os.path.join(upload_dir, unique_filename)
            
            async with aiofiles.open(file_path, 'wb') as out_file:
                content = await file.read()
                await out_file.write(content)
            
            db_file_path = f"/{file_path}"
            
            await db.execute("UPDATE content SET media_url = $1 WHERE id = $2", db_file_path, content_item_id)
            return {"message": "Teaser content uploaded successfully", "media_url": db_file_path}
        else:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Content item not found anywhere")

    if not layer:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Content item not found")

    content_plan = json.loads(layer['content_plan'])
    item_found = False
    updated_media_url = None

    # Define upload directory based on layer
    upload_dir = os.path.join("uploads", str(layer['character_id']), "layers", str(layer['id']), "content")
    os.makedirs(upload_dir, exist_ok=True)
    file_extension = file.filename.split('.')[-1]
    unique_filename = f"{content_item_id}.{file_extension}"
    file_path = os.path.join(upload_dir, unique_filename)

    async with aiofiles.open(file_path, 'wb') as out_file:
        content = await file.read()
        await out_file.write(content)
    
    updated_media_url = f"/{file_path}"

    for content_type in ['photo_prompts', 'video_prompts', 'audio_texts']:
        if content_type in content_plan:
            for item in content_plan[content_type]:
                if item['id'] == content_item_id:
                    item['media_url'] = updated_media_url
                    item_found = True
                    break
        if item_found:
            break

    if not item_found:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Content item not found in content plan")

    # Update the content_plan in the database
    update_query = """
        UPDATE layers
        SET content_plan = $1
        WHERE id = $2
        RETURNING *
    """
    updated_layer = await db.fetchrow(update_query, json.dumps(content_plan), layer['id'])

    return updated_layer
