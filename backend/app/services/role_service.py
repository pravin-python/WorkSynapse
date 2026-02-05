from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import or_, desc, func, select
from sqlalchemy.orm import selectinload
from fastapi import HTTPException, status

from app.models.user.model import Role, Permission
from app.schemas.role import RoleCreate, RoleUpdate

class RoleService:
    async def get_list(
        self, 
        db: AsyncSession, 
        skip: int = 0, 
        limit: int = 100, 
        search: Optional[str] = None,
        is_system: Optional[bool] = None  # Added filter
    ) -> List[Role]:
        # Eager load permissions and users to calculate counts
        query = select(Role).options(selectinload(Role.permissions), selectinload(Role.users))
        
        if search:
            search_term = f"%{search}%"
            query = query.filter(
                or_(
                    Role.name.ilike(search_term),
                    Role.description.ilike(search_term)
                )
            )

        if is_system is not None:
            query = query.filter(Role.is_system == is_system)
            
        query = query.order_by(desc(Role.id)).offset(skip).limit(limit)
        result = await db.execute(query)
        roles = result.scalars().all()
        
        # Attach users_count to each role instance for the Pydantic schema
        for role in roles:
            setattr(role, 'users_count', len(role.users))
            
        return roles

    async def get_count(self, db: AsyncSession, search: Optional[str] = None, is_system: Optional[bool] = None) -> int:
        query = select(func.count(Role.id))
        
        if search:
            search_term = f"%{search}%"
            query = query.filter(
                or_(
                    Role.name.ilike(search_term),
                    Role.description.ilike(search_term)
                )
            )

        if is_system is not None:
            query = query.filter(Role.is_system == is_system)
            
        result = await db.execute(query)
        return result.scalar()

    async def get_by_id(self, db: AsyncSession, role_id: int) -> Optional[Role]:
        query = select(Role).options(selectinload(Role.permissions), selectinload(Role.users)).filter(Role.id == role_id)
        result = await db.execute(query)
        role = result.scalars().first()
        if role:
            setattr(role, 'users_count', len(role.users))
        return role

    async def get_by_name(self, db: AsyncSession, name: str) -> Optional[Role]:
        query = select(Role).filter(Role.name == name)
        result = await db.execute(query)
        return result.scalars().first()

    async def create(self, db: AsyncSession, role_in: RoleCreate) -> Role:
        # Check if role exists
        if await self.get_by_name(db, role_in.name):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Role with name '{role_in.name}' already exists"
            )
            
        # Get permissions
        permissions = []
        if role_in.permission_ids:
            result = await db.execute(select(Permission).filter(Permission.id.in_(role_in.permission_ids)))
            permissions = result.scalars().all()
            if len(permissions) != len(role_in.permission_ids):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="One or more permission IDs are invalid"
                )
        
        db_role = Role(
            name=role_in.name,
            description=role_in.description,
            permissions=permissions
        )
        
        db.add(db_role)
        await db.commit()
        await db.refresh(db_role)
        # Verify it has users_count for response
        setattr(db_role, 'users_count', 0)
        return db_role

    async def update(self, db: AsyncSession, role: Role, role_in: RoleUpdate) -> Role:
        # Update basic fields
        if role_in.name is not None and role_in.name != role.name:
            if await self.get_by_name(db, role_in.name):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Role with name '{role_in.name}' already exists"
                )
            role.name = role_in.name
            
        if role_in.description is not None:
            role.description = role_in.description
            
        # Update permissions if provided
        if role_in.permission_ids is not None:
            result = await db.execute(select(Permission).filter(Permission.id.in_(role_in.permission_ids)))
            permissions = result.scalars().all()
            if len(permissions) != len(role_in.permission_ids):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="One or more permission IDs are invalid"
                )
            role.permissions = permissions
            
        db.add(role)
        await db.commit()
        await db.refresh(role)
        
        # Reload to get users count properly or just set it if we know
        # For simplicity, we can do a quick load or just assume 0 change in users during update
        # But best to reload if we want accuracy.
        # However, update receives 'role' which might be detached or attached.
        # Let's just re-fetch to be safe and consistent.
        return await self.get_by_id(db, role.id)

    async def delete(self, db: AsyncSession, role: Role) -> Role:
        if role.is_system:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="System roles cannot be deleted"
            )
            
        await db.delete(role)
        await db.commit()
        return role

    async def get_all_permissions(self, db: AsyncSession) -> List[Permission]:
        result = await db.execute(select(Permission).order_by(Permission.resource, Permission.action))
        return result.scalars().all()


role_service = RoleService()
