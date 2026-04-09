from fastapi import APIRouter, Depends, HTTPException, status
from asyncpg.exceptions import UniqueViolationError
from api.database.connection import get_db
import uuid
from pydantic import BaseModel
from typing import List, Optional
import json

router = APIRouter(
    prefix="/admin/comfy-workflows",
    tags=["comfy-workflows"]
)

class ComfyWorkflowBase(BaseModel):
    name: str
    description: Optional[str] = None
    workflow_data: dict
    is_active: bool = False

class ComfyWorkflowCreate(ComfyWorkflowBase):
    pass

class ComfyWorkflowUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    workflow_data: Optional[dict] = None
    is_active: Optional[bool] = None

class ComfyWorkflowInDB(ComfyWorkflowBase):
    id: uuid.UUID
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True

@router.get("/", response_model=List[ComfyWorkflowInDB], summary="Get all ComfyUI workflows")
async def get_all_comfy_workflows(db=Depends(get_db)):
    query = "SELECT id, name, description, workflow_data, is_active, created_at, updated_at FROM comfy_workflows ORDER BY created_at DESC"
    records = await db.fetch(query)
    # Manually parse the workflow_data from JSON string to dict
    workflows = []
    for record in records:
        record_dict = dict(record)
        if isinstance(record_dict['workflow_data'], str):
            record_dict['workflow_data'] = json.loads(record_dict['workflow_data'])
        # Convert datetime objects to string
        record_dict['created_at'] = str(record_dict['created_at'])
        record_dict['updated_at'] = str(record_dict['updated_at'])
        workflows.append(record_dict)
    return workflows

@router.post("/", response_model=ComfyWorkflowInDB, status_code=status.HTTP_201_CREATED, summary="Create a new ComfyUI workflow")
async def create_comfy_workflow(workflow: ComfyWorkflowCreate, db=Depends(get_db)):
    query = """INSERT INTO comfy_workflows (name, description, workflow_data, is_active)
               VALUES ($1, $2, $3, $4) RETURNING id, name, description, workflow_data, is_active, created_at, updated_at"""
    try:
        new_workflow_record = await db.fetchrow(
            query,
            workflow.name,
            workflow.description,
            json.dumps(workflow.workflow_data), # Convert dict to JSON string
            workflow.is_active
        )
        # Manually parse the JSONB field before returning
        record_dict = dict(new_workflow_record)
        if isinstance(record_dict['workflow_data'], str):
            record_dict['workflow_data'] = json.loads(record_dict['workflow_data'])
        record_dict['created_at'] = str(record_dict['created_at'])
        record_dict['updated_at'] = str(record_dict['updated_at'])
        return record_dict
    except UniqueViolationError:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="A workflow with this name already exists.")
    except Exception as e:
        print(f"DATABASE ERROR on workflow create: {e}") # Detailed logging
        raise HTTPException(status_code=500, detail=f"Database error: {e}")

@router.get("/{workflow_id}", response_model=ComfyWorkflowInDB, summary="Get a single ComfyUI workflow by ID")
async def get_comfy_workflow_by_id(workflow_id: uuid.UUID, db=Depends(get_db)):
    query = "SELECT id, name, description, workflow_data, is_active, created_at, updated_at FROM comfy_workflows WHERE id = $1"
    workflow = await db.fetchrow(query, workflow_id)
    if not workflow:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workflow not found")
    return workflow

@router.put("/{workflow_id}", response_model=ComfyWorkflowInDB, summary="Update a ComfyUI workflow")
async def update_comfy_workflow(workflow_id: uuid.UUID, workflow_update: ComfyWorkflowUpdate, db=Depends(get_db)):
    update_fields = []
    update_values = []
    arg_counter = 1

    for field, value in workflow_update.model_dump(exclude_unset=True).items():
        update_fields.append(f"{field} = ${arg_counter}")
        # Special handling for JSONB field
        if field == 'workflow_data':
            update_values.append(json.dumps(value)) # Convert dict to JSON string
        else:
            update_values.append(value)
        arg_counter += 1
    
    if not update_fields:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No update data provided.")

    update_fields.append(f"updated_at = NOW()")
    
    query = f"""UPDATE comfy_workflows SET {', '.join(update_fields)} 
               WHERE id = ${arg_counter} RETURNING *"""
    update_values.append(workflow_id)

    try:
        updated_workflow = await db.fetchrow(query, *update_values)
        if not updated_workflow:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workflow not found")
        
        # Manually parse the JSONB field before returning
        record_dict = dict(updated_workflow)
        if isinstance(record_dict['workflow_data'], str):
            record_dict['workflow_data'] = json.loads(record_dict['workflow_data'])
        record_dict['created_at'] = str(record_dict['created_at'])
        record_dict['updated_at'] = str(record_dict['updated_at'])

        return record_dict
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {e}")

@router.delete("/{workflow_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete a ComfyUI workflow")
async def delete_comfy_workflow(workflow_id: uuid.UUID, db=Depends(get_db)):
    # Check if the workflow is active, prevent deletion of active workflow
    workflow = await db.fetchrow("SELECT is_active FROM comfy_workflows WHERE id = $1", workflow_id)
    if not workflow:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workflow not found")
    if workflow['is_active']:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot delete an active workflow. Please set another workflow as active first.")

    result = await db.execute("DELETE FROM comfy_workflows WHERE id = $1", workflow_id)
    if result == "DELETE 0":
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workflow not found during deletion.")
    return

@router.post("/{workflow_id}/set-active", response_model=ComfyWorkflowInDB, summary="Set a workflow as active")
async def set_workflow_active(workflow_id: uuid.UUID, db=Depends(get_db)):
    async with db.acquire() as connection:
        async with connection.transaction():
            # Deactivate all other workflows
            await connection.execute("UPDATE comfy_workflows SET is_active = FALSE WHERE id != $1", workflow_id)
            # Activate the target workflow
            updated_workflow = await connection.fetchrow(
                "UPDATE comfy_workflows SET is_active = TRUE WHERE id = $1 RETURNING *",
                workflow_id
            )
    if not updated_workflow:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workflow not found")
    
    # Manually parse the JSONB field and convert datetimes before returning
    record_dict = dict(updated_workflow)
    if isinstance(record_dict.get('workflow_data'), str):
        record_dict['workflow_data'] = json.loads(record_dict['workflow_data'])
    record_dict['created_at'] = str(record_dict['created_at'])
    record_dict['updated_at'] = str(record_dict['updated_at'])

    return record_dict
