from typing import Any, Dict, List, Optional, Union
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from passlib.context import CryptContext
from app.models.user.model import User, Role, Permission, Session, LoginHistory
from app.services.base import SecureCRUDBase, NotFoundError, ValidationError
from pydantic import BaseModel, EmailStr, field_validator
import re
import datetime

# Password hashing context using bcrypt
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# =============================================================================
# PYDANTIC SCHEMAS
# =============================================================================

class UserCreate(BaseModel):
    """Schema for creating a new user."""
    email: EmailStr
    full_name: str
    password: str
    username: Optional[str] = None
    role_id: Optional[int] = None # Added role_id for dynamic role assignment
    
    @field_validator('password')
    @classmethod
    def validate_password(cls, v: str) -> str:
        """Validate password strength."""
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters')
        if not re.search(r'[A-Z]', v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not re.search(r'[a-z]', v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not re.search(r'\d', v):
            raise ValueError('Password must contain at least one digit')
        # Allow passing special chars check for now if tests are too strict or keep it.
        # But previous validation had it, so let's keep it.
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', v):
             raise ValueError('Password must contain at least one special character')
        return v
    
    @field_validator('full_name')
    @classmethod
    def validate_full_name(cls, v: str) -> str:
        """Validate full name."""
        if len(v.strip()) < 2:
            raise ValueError('Full name must be at least 2 characters')
        if len(v) > 255:
            raise ValueError('Full name must be at most 255 characters')
        return v.strip()
    
    @field_validator('username')
    @classmethod
    def validate_username(cls, v: Optional[str]) -> Optional[str]:
        """Validate username."""
        if v is None:
            return v
        if len(v) < 3:
            raise ValueError('Username must be at least 3 characters')
        if len(v) > 50:
            raise ValueError('Username must be at most 50 characters')
        if not re.match(r'^[a-zA-Z0-9_-]+$', v):
            raise ValueError('Username can only contain letters, numbers, underscores, and hyphens')
        return v.lower()


class UserUpdate(BaseModel):
    """Schema for updating a user."""
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    username: Optional[str] = None
    is_active: Optional[bool] = None
    avatar_url: Optional[str] = None
    timezone: Optional[str] = None
    locale: Optional[str] = None
    role_id: Optional[int] = None # Allow updating role via role_id


class PasswordChange(BaseModel):
    """Schema for changing password."""
    current_password: str
    new_password: str
    
    @field_validator('new_password')
    @classmethod
    def validate_new_password(cls, v: str) -> str:
        """Validate new password strength."""
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters')
        if not re.search(r'[A-Z]', v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not re.search(r'[a-z]', v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not re.search(r'\d', v):
            raise ValueError('Password must contain at least one digit')
        return v


# =============================================================================
# USER SERVICE
# =============================================================================

class UserService(SecureCRUDBase[User, UserCreate, UserUpdate]):
    """
    User management service.
    """
    
    async def create(self, db: AsyncSession, obj_in: UserCreate) -> User:
        """Create a new user with secure password hashing and Role assignment."""
        
        # Check if email exists
        if await self.get_by_email(db, obj_in.email):
            raise ValidationError(f"User with email {obj_in.email} already exists")
            
        # Check if username exists (if provided)
        if obj_in.username and await self.get_by_username(db, obj_in.username):
            raise ValidationError(f"User with username {obj_in.username} already exists")
            
        # Create user dict but exclude role_id from direct mapping if User model doesn't have it as column
        # User model has 'role' enum column, but 'roles' relationship for RBAC.
        # We handle role assignment separately.
        user_data = obj_in.model_dump(exclude={'password', 'role_id'})
        user_data['hashed_password'] = pwd_context.hash(obj_in.password)
        
        db_obj = User(**user_data)
        db.add(db_obj)
        # Flush to get user ID
        await db.flush()
        
        # Handle Role Assignment
        if obj_in.role_id:
            role = await db.get(Role, obj_in.role_id)
            if not role:
                 raise ValidationError(f"Role with id {obj_in.role_id} not found")
            if not role.is_active:
                 raise ValidationError(f"Role with id {obj_in.role_id} is inactive")
            
            # Append role to user's roles
            db_obj.roles.append(role)
        
        await db.commit()
        await db.refresh(db_obj)
        return db_obj
    
    async def update(
        self, 
        db: AsyncSession, 
        *, 
        db_obj: User, 
        obj_in: Union[UserUpdate, Dict[str, Any]]
    ) -> User:
        """Update a user."""
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = obj_in.model_dump(exclude_unset=True)
            
        # Handle password update separately if needed, but Basic UserUpdate doesn't have password. 
        # (It's in UserUpdate schema above but not handled here typically - logic usually checks for it)
        # But wait, UserUpdate schema above DOES NOT have password field initially? 
        # Ah, I see UserUpdate in schemas/user.py has password.
        # The UserUpdate in this file is separate? Checks above.
        # It seems redundant. Best to use single source of truth.
        # However, for this task, let's focus on role update.
        
        role_id = update_data.pop('role_id', None)
        
        # Update standard fields
        # Call super().update logic or manual
        for field, value in update_data.items():
            if hasattr(db_obj, field):
                setattr(db_obj, field, value)
        
        # Handle Role mapping update if provided
        if role_id is not None:
             # Logic: Replace existing roles or add? 
             # Requirement: "Staff users must have exactly one role" implied for this flow.
             # Let's start by clearing existing and setting new, or just appending?
             # For a dropdown selection, it usually implies "The Role".
             role = await db.get(Role, role_id)
             if role and role.is_active:
                 db_obj.roles = [role] # Replace all roles with this one for simplicity and alignment with single dropdown
        
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def authenticate(
        self, 
        db: AsyncSession, 
        *, 
        email: str, 
        password: str
    ) -> Optional[User]:
        """Authenticate a user."""
        user = await self.get_by_email(db, email=email)
        if not user:
            return None
        if not self.verify_password(password, user.hashed_password):
            return None
        return user
    
    async def get_by_email(self, db: AsyncSession, *, email: str) -> Optional[User]:
        """Get user by email."""
        result = await db.execute(select(User).filter(User.email == email))
        return result.scalars().first()
    
    async def get_by_username(self, db: AsyncSession, *, username: str) -> Optional[User]:
        """Get user by username."""
        result = await db.execute(select(User).filter(User.username == username))
        return result.scalars().first()
        
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify a password."""
        return pwd_context.verify(plain_password, hashed_password)
    
    def get_password_hash(self, password: str) -> str:
        """Hash a password."""
        return pwd_context.hash(password)


user_service = UserService(User)
