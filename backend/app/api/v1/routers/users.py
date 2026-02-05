from typing import Any, List
from fastapi import APIRouter, Body, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database.session import get_db
from app.models.user.model import User, Role
from app.schemas.user import User as UserSchema, UserUpdate
from app.services.user import user_service
from app.api.deps import get_current_user, get_current_active_superuser, require_roles
# Switched import to app.api.deps to align with other routers and ensure we are using the updated dependency

router = APIRouter()

@router.get("/me", response_model=UserSchema)
async def read_user_me(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Get current user.
    """
    # Eager load roles and permissions for Pydantic serialization
    # Pydantic schema expects 'roles' and 'permissions' which access relationships
    # We must explicitly load them here to avoid async loading errors
    
    # We use populate_existing to update the current instance in the session
    # or just fetch a fresh one. Fetching fresh is safer/cleaner.
    from sqlalchemy import select
    query = select(User).options(
        selectinload(User.roles).selectinload(Role.permissions)
    ).filter(User.id == current_user.id)
    
    result = await db.execute(query)
    user = result.scalars().first()
    return user

@router.get("/", response_model=List[UserSchema])
async def read_users(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_active_superuser),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Retrieve users.
    """
    # For list, we might want to eager load too if we display roles
    # But usually list view is simpler. Let's start with basic list.
    # If frontend User list needs roles, we should update this too.
    # Assuming user_service.get_multi can handle it or we update it here.
    # Let's trust user_service for now or update it to be safe?
    # user_service.get_multi probably doesn't eager load.
    # Let's override for this specific route.
    from sqlalchemy import select
    
    query = select(User).options(
        selectinload(User.roles).selectinload(Role.permissions)
    ).offset(skip).limit(limit)
    
    result = await db.execute(query)
    users = result.scalars().all()
    return users
