from typing import Optional, List
from pydantic import BaseModel, EmailStr, Field, computed_field
from app.models.user.model import UserRole

class UserBase(BaseModel):
    email: EmailStr
    full_name: str
    is_active: Optional[bool] = True
    role: UserRole = UserRole.DEVELOPER
    is_superuser: bool = False

class UserCreate(UserBase):
    password: str

class UserUpdate(UserBase):
    password: Optional[str] = None

class User(UserBase):
    id: int
    
    class Config:
        from_attributes = True

    @computed_field
    def roles(self) -> List[str]:
        # Return list of role names
        if not hasattr(self, 'user_roles') and not hasattr(self, '_sa_instance_state'):
             # If it's a dict or partial object
             return []
        # Accessing the relationship directly
        # Note: 'roles' relationship on User model returns Role objects
        try:
            return [r.name for r in getattr(self, "roles", [])]
        except:
            return []

    @computed_field
    def permissions(self) -> List[str]:
        # Return set of unique permission strings "resource:action"
        perms = set()
        try:
            for role in getattr(self, "roles", []):
                for perm in role.permissions:
                    # Format: "resource:action" matches how frontend usually checks, 
                    # OR just return action names? 
                    # The frontend hasPermission checks: state.user.permissions?.includes(permission)
                    # Use "resource.action" or just action? 
                    # Let's check frontend usage.
                    # Frontend usually expects "action" or "resource:action". 
                    # Given RoleForm uses specific Permissions, let's return a combined string.
                    # But wait, looking at RoleForm, permission has `action` and `resource`.
                    # Let's return `${resource}:${action}` and maybe just `${action}` if unique?
                    # Let's verify what frontend expects.
                    # AuthContext: hasPermission(permission). 
                    # If I look at usage in sidebar: no specific usage seen yet.
                    # Let's stick to "resource:action" as a safe bet, or simple list of actions.
                    # Actually, let's just use the permission 'action' value for now if that's what's used,
                    # but typically RBAC is resource:action.
                    # Let's assume the frontend might use "manage_roles" (which might be an action).
                    # For safety, let's include "resource:action" AND "action".
                    perms.add(f"{perm.resource}:{perm.action.value}") 
                    perms.add(perm.action.value)
        except:
            pass
        return list(perms)
