
import time
import asyncio
import json
import logging
import os
import copy
import random
from typing import Optional, Any
import uuid

import aiohttp
from api.database.connection import get_db

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

COMFYUI_URL = os.getenv("COMFYUI_URL", "https://harmony-superwrought-unprofessorially.ngrok-free.dev")

class ComfyService:
    def __init__(self):
        self.comfy_url = COMFYUI_URL

    async def _load_active_workflow(self):
        """
        Loads the active workflow from the database and transforms it into the format
        required by the ComfyUI API.
        """
        logger.info("Attempting to load active ComfyUI workflow from database...")
        db_gen = get_db()
        db_pool = await anext(db_gen)
        try:
            async with db_pool.acquire() as connection:
                record = await connection.fetchrow(
                    "SELECT workflow_data FROM comfy_workflows WHERE is_active = TRUE LIMIT 1"
                )
                if not (record and record['workflow_data']):
                    logger.error("No active ComfyUI workflow configured in the database!")
                    raise Exception("No active ComfyUI workflow configured.")

                logger.info("Active workflow found. Transforming to API format...")
                ui_workflow = json.loads(record['workflow_data'])
                
                api_prompt = {}
                nodes_by_id = {str(node['id']): node for node in ui_workflow['nodes']}

                # This mapping defines the correct order of widget inputs for specific node types.
                # It is used to correctly parse the `widgets_values` array from the UI workflow,
                # as the UI workflow data does not contain the names for widget inputs.
                WIDGET_MAPPING = {
                    "CheckpointLoaderSimple": ["ckpt_name"],
                    "CLIPTextEncode": ["text"],
                    "EmptyLatentImage": ["width", "height", "batch_size"],
                    "ImageScale": ["upscale_method", "width", "height", "crop"],
                    "ReActorFaceSwap": ["enabled", "swap_model", "facedetection", "face_restore_model", "face_restore_visibility", "codeformer_weight", "detect_gender_input", "detect_gender_source", "input_faces_index", "source_faces_index", "console_log_level"],
                    "Image Saver Simple": ["filename_prefix", "filename_delimiter", "extension", "save_metadata", "quality", "save_workflow", "embed_workflow", "lossless_webp", "counter_digits", "time_format", "overwrite_existing"],
                    "LoadImage": ["image", "upload"],
                    "VRAMCleanup": ["offload_model", "offload_cache"],
                    "RAMCleanup": ["clean_file_cache", "clean_dlls", "clean_processes", "retry_times"],
                    "IPAdapterModelLoader": ["ipadapter_file"],
                    "UnetLoaderGGUF": ["unet_name"],
                    "CLIPVisionLoader": ["clip_name"],
                    "IPAdapterInsightFaceLoader": ["provider", "model_name"],
                    "IPAdapterFaceID": ["weight", "weight_faceidv2", "combine_embeds", "start_at", "end_at", "embeds_scaling"],
                    # KSampler is handled by its own special logic below and does not need to be in this map.
                }

                # Pass 1: Initialize nodes and populate with widget values
                for node_id, node_data in nodes_by_id.items():
                    if node_data.get('type') == 'Note':
                        continue

                    api_inputs = {}
                    widget_values = node_data.get("widgets_values", [])
                    node_type = node_data.get('type')

                    # --- Start of New Widget Processing Logic ---

                    # Special case for KSampler, as its widget order is complex
                    if node_type == 'KSampler' and widget_values and len(widget_values) >= 7:
                        # KSampler widget_values from UI: [seed, control_after_generate, steps, cfg, sampler_name, scheduler, denoise]
                        
                        seed = widget_values[0]
                        control_after_generate = widget_values[1]
                        
                        # If control is set to randomize, generate a new random seed
                        if control_after_generate == 'randomize':
                            seed = random.randint(0, 0xffffffffffffffff) # Generate a 64-bit seed
                            logger.info(f"  [KSampler Special] Randomized seed to: {seed}")

                        api_inputs["seed"] = seed
                        api_inputs["steps"] = int(widget_values[2])
                        api_inputs["cfg"] = float(widget_values[3])
                        api_inputs["sampler_name"] = widget_values[4]
                        api_inputs["scheduler"] = widget_values[5]
                        api_inputs["denoise"] = float(widget_values[6])
                        logger.info(f"  [KSampler Special] Mapped inputs: {api_inputs}")

                    # Generic case using the WIDGET_MAPPING
                    elif node_type in WIDGET_MAPPING:
                        input_names = WIDGET_MAPPING[node_type]
                        if len(widget_values) >= len(input_names):
                            for i, name in enumerate(input_names):
                                # Simple type conversion for known types
                                value = widget_values[i]
                                if isinstance(value, str) and value.lower() in ['true', 'false']:
                                    api_inputs[name] = value.lower() == 'true'
                                elif isinstance(value, (int, float)):
                                    api_inputs[name] = value
                                else: # Assume string or other valid type
                                    api_inputs[name] = value
                            logger.info(f"  [{node_type} Mapped] Mapped {len(api_inputs)} inputs via WIDGET_MAPPING.")
                        else:
                            logger.warning(f"  [{node_type} Mapped] Mismatch: Expected {len(input_names)} widgets, but found {len(widget_values)}.")

                    # --- End of New Widget Processing Logic ---

                    # --- Patch for Image Saver Simple due to API vs UI input name mismatch ---
                    if node_type == 'Image Saver Simple':
                        logger.info(f"  Patching inputs for Image Saver Simple (Node {node_id})...")
                        # The server expects 'filename', but the UI provides 'filename_prefix'.
                        if 'filename_prefix' in api_inputs and 'filename' not in api_inputs:
                            # Let's not use pop, just assign, to be safe.
                            api_inputs['filename'] = api_inputs['filename_prefix']
                            logger.info(f"    - Patched 'filename' with value from 'filename_prefix'.")

                        # Add other missing fields with default values that the server requires.
                        if 'optimize_png' not in api_inputs:
                            api_inputs['optimize_png'] = False
                            logger.info(f"    - Patched missing 'optimize_png' with default: False")
                        if 'quality_jpeg_or_webp' not in api_inputs:
                            api_inputs['quality_jpeg_or_webp'] = 100
                            logger.info(f"    - Patched missing 'quality_jpeg_or_webp' with default: 100")
                        if 'save_workflow_as_json' not in api_inputs:
                            api_inputs['save_workflow_as_json'] = False
                            logger.info(f"    - Patched missing 'save_workflow_as_json' with default: False")
                        if 'path' not in api_inputs:
                            api_inputs['path'] = ""
                            logger.info(f"    - Patched missing 'path' with default: ''")

                    # --- Patch for IPAdapterFaceID to correct mapped values ---
                    if node_type == 'IPAdapterFaceID':
                        logger.info(f"  Smart-Patching inputs for IPAdapterFaceID (Node {node_id})...")
                        
                        # Correct string values that might be mapped incorrectly from UI dropdowns
                        if api_inputs.get('combine_embeds') == 'linear':
                            api_inputs['combine_embeds'] = 'concat'
                            logger.info(f"    - Patched 'combine_embeds' from 'linear' to 'concat'.")
                        if str(api_inputs.get('embeds_scaling')) == '1':
                            api_inputs['embeds_scaling'] = 'V only'
                            logger.info(f"    - Patched 'embeds_scaling' from '1' to 'V only'.")

                        # Ensure required fields that might be missing are added
                        if 'weight_type' not in api_inputs:
                            api_inputs['weight_type'] = 'linear'
                            logger.info(f"    - Patched missing 'weight_type' with default: 'linear'.")

                        # Final check to ensure all numeric fields are actually floats
                        for key in ['weight', 'weight_faceidv2', 'start_at', 'end_at']:
                            if key in api_inputs:
                                try:
                                    api_inputs[key] = float(api_inputs[key])
                                except (ValueError, TypeError):
                                    default_val = 1.0 if 'weight' in key else (0.0 if 'start' in key else 1.0)
                                    logger.warning(f"    ! Could not convert '{key}' to float. Reverting to default {default_val}.")
                                    api_inputs[key] = default_val
                        logger.info(f"    - Final Patched Inputs: {api_inputs}")


                    # --- End of Patch ---

                    api_prompt[node_id] = {
                        "class_type": node_type,
                        "inputs": api_inputs
                    }

                # Pass 2: Create connections by processing the global links array
                for link_info in ui_workflow.get('links', []):
                    try:
                        # link_info format: [link_id, source_node_id, source_slot, target_node_id, target_slot, type]
                        source_node_id = str(link_info[1])
                        source_slot = link_info[2]
                        target_node_id = str(link_info[3])
                        target_slot = link_info[4]

                        # Find the name of the input on the target node
                        target_node_data = nodes_by_id.get(target_node_id)
                        if target_node_data and 'inputs' in target_node_data and len(target_node_data['inputs']) > target_slot:
                            input_name = target_node_data['inputs'][target_slot]['name']
                            
                            # Add the link to the corresponding input in the api_prompt
                            if target_node_id in api_prompt:
                                api_prompt[target_node_id]['inputs'][input_name] = [source_node_id, source_slot]
                        else:
                            logger.warning(f"Could not find target input for link: {link_info}")
                    except (IndexError, KeyError) as e:
                        logger.error(f"Error processing link: {link_info}. Error: {e}")

                logger.info(f"Workflow transformed successfully with {len(api_prompt)} nodes")
                return api_prompt
        finally:
            await db_gen.aclose()

    async def generate_image_with_face(self, text_prompt: str, face_image_bytes: bytes):
        active_workflow = await self._load_active_workflow()
        if not active_workflow:
            raise Exception("Failed to load active workflow.")

        # Debug: Log all nodes in the transformed workflow
        logger.info(f"Transformed workflow nodes: {list(active_workflow.keys())}")
        for node_id, node in active_workflow.items():
            logger.info(f"Node {node_id}: class_type={node.get('class_type')}")

        try:
            # Generate a unique filename to prevent server-side conflicts
            unique_filename = f"reference_face_{int(time.time())}.jpg"
            logger.info(f"--- UPLOAD: Attempting to upload reference image as {unique_filename}... ---")
            upload_response = await self.upload_image(face_image_bytes, unique_filename)
            logger.info("--- UPLOAD: Image upload successful. ---")
            uploaded_face_filename = upload_response['name']
            logger.info(f"Image uploaded to ComfyUI: {upload_response}")

            # Find key nodes and the final save node connected to ReActor
            prompt_node_id = None
            load_image_node_id = None
            reactor_node_id = None
            final_save_node_id = None

            # First, find the ReActor node ID
            for node_id, node in active_workflow.items():
                if node['class_type'] == 'ReActorFaceSwap':
                    reactor_node_id = node_id
                    logger.info(f"Found ReActorFaceSwap node: {reactor_node_id}")
                    break

            if not reactor_node_id:
                raise Exception("ReActorFaceSwap node not found in workflow.")

            # Then, trace the output of the ReActor node to find the final Save node
            # This requires access to the original UI workflow to trace links
            db_gen = get_db()
            db = await anext(db_gen)
            try:
                ui_workflow_data = await db.fetchrow("SELECT workflow_data FROM comfy_workflows WHERE is_active = TRUE LIMIT 1")
                if not ui_workflow_data:
                    raise Exception("No active workflow found in database.")
                
                ui_workflow = json.loads(ui_workflow_data['workflow_data'])
                nodes_by_id = {str(node['id']): node for node in ui_workflow['nodes']}
                
                for link_info in ui_workflow.get('links', []):
                    source_node_id = str(link_info[1])
                    if source_node_id == reactor_node_id:
                        target_node_id = str(link_info[3])
                        target_node = nodes_by_id.get(target_node_id)
                        if target_node and target_node.get('type') in ['SaveImage', 'Image Saver Simple']:
                            final_save_node_id = target_node_id
                            logger.info(f"Found final SaveImage node connected to ReActor: {final_save_node_id}")
                            break # Assume first found is the correct one
            finally:
                await db_gen.aclose()
            
            if not final_save_node_id:
                raise Exception("Could not find a SaveImage node connected to the ReActorFaceSwap node.")

            # Find the KSampler to identify the correct positive prompt node
            ksampler_node_id = None
            for node_id, node in active_workflow.items():
                if node['class_type'] == 'KSampler':
                    ksampler_node_id = node_id
                    break
            
            if not ksampler_node_id:
                raise Exception("KSampler node not found in workflow.")

            positive_input = active_workflow[ksampler_node_id]['inputs'].get('positive')
            if not positive_input or not isinstance(positive_input, list):
                raise Exception("Could not find positive prompt connection to KSampler.")
            prompt_node_id = positive_input[0]

            # Find the first LoadImage node (this has been a stable approach)
            load_image_node_id = None
            for node_id, node in active_workflow.items():
                if node['class_type'] == 'LoadImage':
                    load_image_node_id = node_id
                    break

            if not all([prompt_node_id, load_image_node_id]):
                raise Exception(f"Missing required positive prompt connection or LoadImage node.")

            logger.info(f"Found nodes -> Prompt: {prompt_node_id}, LoadImage: {load_image_node_id}, Final Save: {final_save_node_id}")

            workflow_to_queue = copy.deepcopy(active_workflow)

            # Update the text prompt
            workflow_to_queue[prompt_node_id]["inputs"]["text"] = text_prompt
            
            # Update the image filename
            workflow_to_queue[load_image_node_id]["inputs"]["image"] = uploaded_face_filename
            
            # Update save filename prefix
            workflow_to_queue[final_save_node_id]["inputs"]["filename_prefix"] = "FaceSwap_Result"

            # Queue the prompt
            prompt_id = await self.queue_prompt(workflow_to_queue)
            logger.info(f"Prompt queued with ID: {prompt_id}")

            # --- FINAL DEBUG: Log the exact payload being sent ---
            logger.info(f"--- FINAL PROMPT PAYLOAD ---\n{json.dumps(workflow_to_queue, indent=2)}")
            # --- END FINAL DEBUG ---

            # Wait for and return the result
            final_image_bytes = await self.wait_for_result(prompt_id, final_save_node_id)
            return final_image_bytes

        except Exception as e:
            logger.error(f"Error in image generation process: {e}", exc_info=True)
            return None

    async def upload_image(self, image_bytes: bytes, filename: str) -> dict:
        """Upload an image to ComfyUI and return the server response."""
        url = f"{self.comfy_url}/upload/image"
        headers = {"ngrok-skip-browser-warning": "true"}
        
        with aiohttp.MultipartWriter('form-data') as writer:
            part = writer.append(image_bytes, {
                'Content-Disposition': f'form-data; name="image"; filename="{filename}"',
                'Content-Type': 'image/jpeg'
            })
            
            async with aiohttp.ClientSession(headers=headers) as session:
                async with session.post(url, data=writer) as response:
                    if response.status == 200:
                        return await response.json()
                    error_text = await response.text()
                    logger.error(f"Error uploading image to ComfyUI: {error_text}")
                    raise Exception(f"Image upload failed: {response.status} - {error_text}")

    async def queue_prompt(self, prompt_workflow: dict) -> str:
        url = f"{self.comfy_url}/prompt"
        payload = {"prompt": prompt_workflow}
        headers = {"ngrok-skip-browser-warning": "true"}
        
        async with aiohttp.ClientSession(headers=headers) as session:
            async with session.post(url, json=payload) as response:
                if response.status == 200:
                    return (await response.json()).get('prompt_id')
                error_text = await response.text()
                logger.error(f"Error from ComfyUI server: {error_text}")
                raise Exception(f"Queue prompt failed: {response.status} - {error_text}")

    async def get_history(self, prompt_id: str) -> Optional[dict[str, Any]]:
        url = f"{self.comfy_url}/history/{prompt_id}"
        headers = {"ngrok-skip-browser-warning": "true"}
        async with aiohttp.ClientSession(headers=headers) as session:
            async with session.get(url) as response:
                return await response.json() if response.status == 200 else None

    async def get_image_bytes(self, filename: str, subfolder: str, file_type: str) -> bytes:
        url = f"{self.comfy_url}/view?filename={filename}&subfolder={subfolder}&type={file_type}"
        headers = {"ngrok-skip-browser-warning": "true"}
        async with aiohttp.ClientSession(headers=headers) as session:
            async with session.get(url, timeout=60) as response:
                if response.status == 200:
                    return await response.read()
                raise Exception(f"Failed to get image bytes: {response.status}")

    async def wait_for_result(self, prompt_id: str, save_node_id: str) -> Optional[bytes]:
        while True:
            await asyncio.sleep(2)
            history = await self.get_history(prompt_id)
            if history and prompt_id in history:
                outputs = history[prompt_id].get('outputs', {})
                if outputs and save_node_id in outputs and 'images' in outputs[save_node_id]:
                    image_data = outputs[save_node_id]['images'][0]
                    if image_data['type'] == 'output':
                        logger.info(f"Found final image in node {save_node_id}.")
                        return await self.get_image_bytes(image_data['filename'], image_data.get('subfolder', ''), image_data.get('type'))
                logger.info(f"Waiting for output from prompt ID: {prompt_id}...")
