from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db
from app.services.role_service import role_service
from app.schemas.role import RoleCreate, RoleUpdate, RoleResponse, RoleListResponse, Permission
from app.api.deps import require_admin
from app.models.user.model import User

router = APIRouter()

@router.get("", response_model=RoleListResponse)
async def list_roles(
    skip: int = 0,
    limit: int = 100,
    search: Optional[str] = None,
    is_system: Optional[bool] = None,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """
    List all roles (Admin only).
    """
    roles = await role_service.get_list(db, skip=skip, limit=limit, search=search, is_system=is_system)
    total = await role_service.get_count(db, search=search, is_system=is_system)
    return {"total": total, "items": roles}

@router.post("", response_model=RoleResponse)
async def create_role(
    role_in: RoleCreate,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new role (Admin only).
    """
    return await role_service.create(db, role_in)

@router.get("/permissions", response_model=List[Permission])
async def list_permissions(
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """
    List all available permissions (Admin only).
    """
    return await role_service.get_all_permissions(db)

@router.get("/{role_id}", response_model=RoleResponse)
async def get_role(
    role_id: int,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """
    Get a specific role by ID.
    """
    role = await role_service.get_by_id(db, role_id)
    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Role not found"
        )
    return role

@router.put("/{role_id}", response_model=RoleResponse)
async def update_role(
    role_id: int,
    role_in: RoleUpdate,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """
    Update a role (Admin only).
    """
    role = await role_service.get_by_id(db, role_id)
    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Role not found"
        )
    return await role_service.update(db, role, role_in)

@router.delete("/{role_id}", response_model=RoleResponse)
async def delete_role(
    role_id: int,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """
    Delete a role (Admin only).
    """
    role = await role_service.get_by_id(db, role_id)
    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Role not found"
        )
    return await role_service.delete(db, role)
