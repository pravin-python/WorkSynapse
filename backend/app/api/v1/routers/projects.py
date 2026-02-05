from typing import Any, List
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api import deps
from app.services.project_service import project_service
from app.schemas.project import Project

router = APIRouter()

@router.get("/", response_model=List[Project])
async def read_projects(
    db: AsyncSession = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
    current_user: Any = Depends(deps.get_current_active_user),
) -> Any:
    """
    Retrieve projects.
    """
    projects = await project_service.get_multi(db, skip=skip, limit=limit)
    return projects
