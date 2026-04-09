import logging
import uuid
import os
import json
import aiofiles
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from api.database.connection import get_db
from api.services.image_generator import OpenRouterImageGenerator
from api.services.comfy_service import ComfyService
from api.auth.security import role_required

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/content",
    tags=["content_generation"],
)

class GenerationRequest(BaseModel):
    character_id: uuid.UUID
    content_item_id: str
    prompt: str
    model: str = 'google/gemini-3.1-flash-image-preview' # Add model selection

@router.post("/generate-photo")
async def generate_photo_for_content_item(request: GenerationRequest, db=Depends(get_db)):
    print(f"--- DEBUG: Received generation request: {request.model_dump_json(indent=2)} ---")
    # 1. Find the character's master reference photo.
    # It could be an uploaded one or a generated one.
    ref_photo_query = """
    SELECT media_url FROM reference_photos 
    WHERE character_id = $1 
    ORDER BY 
        CASE 
            WHEN description = 'Визуальный эталон (загружено)' THEN 1
            WHEN description = 'Эталонное фото (сгенерировано)' THEN 2
            WHEN description = 'Анфас, нейтральное выражение' THEN 3
            ELSE 4
        END,
        created_at ASC
    LIMIT 1
    """
    ref_photo_record = await db.fetchrow(ref_photo_query, request.character_id)
    if not ref_photo_record or not ref_photo_record['media_url']:
        raise HTTPException(status_code=404, detail="Reference photo for character not found.")
    
    base_dir = os.getcwd() # Should be /opt/EVA_AI
    reference_photo_path = os.path.join(base_dir, ref_photo_record['media_url'].lstrip('/'))
    
    if not os.path.exists(reference_photo_path):
         raise HTTPException(status_code=404, detail=f"Reference photo file not found at path: {reference_photo_path}")

    image_bytes = None

    # --- NEW: Route generation based on model ---
    if request.model.upper() == "COMFY":
        print("--- DEBUG: Routing to ComfyService for generation ---")
        try:
            comfy_service = ComfyService()

            # Read the reference photo into bytes for the service
            async with aiofiles.open(reference_photo_path, 'rb') as f:
                face_image_bytes = await f.read()

            # Generate the image. The service now returns bytes.
            image_bytes = await comfy_service.generate_image_with_face(
                text_prompt=request.prompt,
                face_image_bytes=face_image_bytes
            )

            if not image_bytes:
                raise Exception("ComfyUI generation failed to return image bytes.")
            
            print(f"--- DEBUG: ComfyUI successfully generated image bytes ---")

        except Exception as e:
            print(f"!!! COMFY GENERATION FAILED: {e} !!!")
            raise HTTPException(status_code=500, detail=f"ComfyUI Generation error: {str(e)}")
    else:
        # --- EXISTING OpenRouter LOGIC ---
        print(f"--- DEBUG: Routing to OpenRouter for generation (model: {request.model}) ---")
        openrouter_api_key = os.getenv("OPENROUTER_API_KEY")
        generator = OpenRouterImageGenerator(api_key=openrouter_api_key)

        try:
            image_bytes = await generator.generate_with_reference(
                model=request.model,
                reference_photo_path=reference_photo_path,
                prompt=request.prompt
            )
        except Exception as e:
            print(f"Image generation failed: {e}")
            error_detail = str(e)
            if hasattr(e, 'response') and e.response:
                try:
                    error_detail = e.response.json().get("error", {}).get("message", str(e))
                except (json.JSONDecodeError, AttributeError):
                    error_detail = e.response.text
            raise HTTPException(status_code=500, detail=f"Generation error: {error_detail}")

    if not image_bytes:
        raise HTTPException(status_code=500, detail="Image generation failed for both routes.")

    # 4. Determine target and save the image
    logger.info(f"--- SAVING PROCESS: Starting save for content_item_id: {request.content_item_id} ---")
    # Check if the content_item_id is a teaser first
    teaser_item = await db.fetchrow("SELECT * FROM content WHERE id = $1 AND subtype = 'teaser'", request.content_item_id)
    
    if teaser_item:
        logger.info(f"--- SAVING PROCESS: Found as a teaser. Saving to teaser directory. ---")
        # It's a teaser photo, save to the teaser directory
        content_upload_dir = os.path.join("uploads", str(request.character_id), "content")
        os.makedirs(content_upload_dir, exist_ok=True)
        file_name = f"{request.content_item_id}.png"
        file_path = os.path.join(content_upload_dir, file_name)

        with open(file_path, "wb") as f:
            f.write(image_bytes)
        
        db_file_path = f"/{file_path}"

        # Update the content table with the new URL, but keep it locked
        logger.info(f"--- SAVING PROCESS: Updating content table for teaser with URL: {db_file_path} ---")
        await db.execute(
            "UPDATE content SET media_url = $1 WHERE id = $2",
            db_file_path, request.content_item_id
        )

        return {"message": "Teaser photo generated successfully", "media_url": db_file_path, "is_locked": True}
    
    # If not a teaser, it's a layer-based content item, proceed with original logic
    logger.info(f"--- SAVING PROCESS: Not a teaser. Searching in layers for character_id: {request.character_id} ---")
    layers = await db.fetch("SELECT id, content_plan FROM layers WHERE character_id = $1", request.character_id)
    
    print(f"--- DEBUG: Found {len(layers)} layers for character {request.character_id} ---")
    print(f"--- DEBUG: Looking for content item ID: {request.content_item_id} ---")
    
    target_layer_id = None
    found = False
    for layer in layers:
        content_plan = json.loads(layer['content_plan']) if isinstance(layer['content_plan'], str) else layer['content_plan']
        logger.info(f"--- SAVING PROCESS: Checking layer {layer['id']}... ---")
        for content_type in ['photo_prompts', 'video_prompts']:
            if content_type in content_plan:
                for item in content_plan[content_type]:
                    logger.debug(f"--- SAVING PROCESS: Comparing {item.get('id')} with {request.content_item_id} ---")
                    if item['id'] == request.content_item_id:
                        target_layer_id = layer['id']
                        found = True
                        logger.info(f"--- SAVING PROCESS: Found content item in layer {layer['id']}! ---")
                        break
            if found:
                break
        if found:
            break
        
    if not target_layer_id:
        logger.error(f"--- SAVING PROCESS FAILED: Content item {request.content_item_id} not found in any layer for character {request.character_id}. ---")
        raise HTTPException(status_code=404, detail="Content item not found in any layer.")

    logger.info(f"--- SAVING PROCESS: Saving to layer {target_layer_id} content directory. ---")
    content_upload_dir = os.path.join("uploads", str(request.character_id), "layers", str(target_layer_id), "content")
    os.makedirs(content_upload_dir, exist_ok=True)

    file_name = f"{request.content_item_id}.png"
    file_path = os.path.join(content_upload_dir, file_name)

    with open(file_path, "wb") as f:
        f.write(image_bytes)
    
    db_file_path = f"/{file_path}"

    # 5. Update the media_url in the database
    logger.info(f"--- SAVING PROCESS: Updating content_plan in layer {target_layer_id} with URL: {db_file_path} ---")
    layer_to_update = await db.fetchrow("SELECT content_plan FROM layers WHERE id = $1", target_layer_id)
    content_plan = json.loads(layer_to_update['content_plan']) if isinstance(layer_to_update['content_plan'], str) else layer_to_update['content_plan']

    updated = False
    for content_type in ['photo_prompts', 'video_prompts']:
        if content_type in content_plan:
            for item in content_plan[content_type]:
                if item['id'] == request.content_item_id:
                    item['media_url'] = db_file_path
                    updated = True
                    break
        if updated:
            break
            
    if not updated:
        logger.error(f"--- SAVING PROCESS FAILED: Failed to find and update content item in layer's content_plan. ---")
        raise HTTPException(status_code=500, detail="Failed to find content item to update.")
        
    await db.execute(
        "UPDATE layers SET content_plan = $1 WHERE id = $2",
        json.dumps(content_plan), target_layer_id
    )

    return {"message": "Image generated successfully", "media_url": db_file_path}


