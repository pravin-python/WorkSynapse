from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime
from app.models.user.model import PermissionAction

# Permission Schemas
class PermissionBase(BaseModel):
    resource: str
    action: PermissionAction
    description: Optional[str] = None
    
class Permission(PermissionBase):
    id: int
    
    class Config:
        from_attributes = True

# Role Schemas
class RoleBase(BaseModel):
    name: str
    description: Optional[str] = None

class RoleCreate(RoleBase):
    permission_ids: List[int]

class RoleUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    permission_ids: Optional[List[int]] = None

class RoleResponse(RoleBase):
    id: int
    is_system: bool
    is_active: bool
    permissions: List[Permission]
    created_at: Optional[datetime] = None
    users_count: int = 0
    
    class Config:
        from_attributes = True

class RoleListResponse(BaseModel):
    total: int
    items: List[RoleResponse]
