from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.session import get_db
from app.api.deps import get_current_user, require_roles
from app.models.user.model import User, UserRole
from app.services.agent_builder_service import AgentBuilderService, AgentBuilderServiceError
from app.schemas.agent_builder import (
    AgentModelCreate, AgentModelUpdate, AgentModelResponse,
    AgentModelResponse
)

router = APIRouter()

@router.get("", response_model=List[AgentModelResponse])
async def list_models(
    provider_id: Optional[int] = None,
    is_active: Optional[bool] = None,
    search: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    List agent models (Admin view).
    """
    models = await AgentBuilderService.get_models(db, provider_id, include_deprecated=True)
    
    # Filter by active status if requested
    if is_active is not None:
        models = [m for m in models if m.is_active == is_active]
        
    # Search filter (in-memory for now, efficient enough for small registry)
    if search:
        search_lower = search.lower()
        models = [
            m for m in models 
            if search_lower in m.name.lower() or search_lower in m.display_name.lower()
        ]
        
    return models

@router.post("", response_model=AgentModelResponse, status_code=status.HTTP_201_CREATED)
async def create_model(
    data: AgentModelCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.ADMIN, UserRole.SUPER_ADMIN]))
):
    """
    Create a new agent model.
    """
    try:
        model = await AgentBuilderService.create_model(db, data)
        return model
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.put("/{model_id}", response_model=AgentModelResponse)
async def update_model(
    model_id: int,
    data: AgentModelUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.ADMIN, UserRole.SUPER_ADMIN]))
):
    """
    Update an agent model.
    """
    try:
        model = await AgentBuilderService.update_model(db, model_id, data)
        if not model:
            raise HTTPException(status_code=404, detail="Model not found")
        return model
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.delete("/{model_id}")
async def delete_model(
    model_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.ADMIN, UserRole.SUPER_ADMIN]))
):
    """
    Soft delete an agent model (sets is_deleted=True).
    To Deprecate/Disable, use UPDATE endpoint.
    """
    try:
        success = await AgentBuilderService.delete_model(db, model_id)
        if not success:
            raise HTTPException(status_code=404, detail="Model not found")
        return {"message": "Model deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
