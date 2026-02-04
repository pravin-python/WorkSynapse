"""
WorkSynapse User Service
========================
User management with secure password handling and RBAC.
"""
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
    User management service with security features.
    
    Features:
    - Secure password hashing (bcrypt)
    - Email validation
    - Password strength enforcement
    - Account lockout
    - Login tracking
    """
    
    def __init__(self):
        super().__init__(User, enable_soft_delete=True, enable_audit_log=True)
    
    # =========================================================================
    # PASSWORD OPERATIONS
    # =========================================================================
    
    @staticmethod
    def hash_password(password: str) -> str:
        """Hash a password using bcrypt."""
        return pwd_context.hash(password)
    
    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash."""
        return pwd_context.verify(plain_password, hashed_password)
    
    # =========================================================================
    # USER CRUD
    # =========================================================================
    
    async def create(
        self,
        db: AsyncSession,
        *,
        obj_in: UserCreate,
        created_by_user_id: Optional[int] = None,
        commit: bool = True,
    ) -> User:
        """
        Create a new user with hashed password.
        """
        # Check for existing email
        existing = await self.get_by_email(db, obj_in.email)
        if existing:
            raise ValidationError("Email already registered")
        
        # Check for existing username
        if obj_in.username:
            existing_username = await self.get_by_username(db, obj_in.username)
            if existing_username:
                raise ValidationError("Username already taken")
        
        # Create user data with hashed password
        user_data = obj_in.model_dump()
        user_data['hashed_password'] = self.hash_password(user_data.pop('password'))
        
        db_obj = User(**user_data)
        db.add(db_obj)
        
        if commit:
            await db.commit()
            await db.refresh(db_obj)
        
        return db_obj
    
    async def get_by_email(
        self,
        db: AsyncSession,
        email: str,
    ) -> Optional[User]:
        """Get user by email address."""
        query = select(User).filter(User.email == email.lower())
        result = await db.execute(query)
        return result.scalars().first()
    
    async def get_by_username(
        self,
        db: AsyncSession,
        username: str,
    ) -> Optional[User]:
        """Get user by username."""
        query = select(User).filter(User.username == username.lower())
        result = await db.execute(query)
        return result.scalars().first()
    
    async def authenticate(
        self,
        db: AsyncSession,
        *,
        email: str,
        password: str,
        ip_address: str,
        user_agent: Optional[str] = None,
    ) -> Optional[User]:
        """
        Authenticate a user by email and password.
        
        Includes:
        - Account lockout check
        - Failed attempt tracking
        - Login history recording
        """
        user = await self.get_by_email(db, email)
        
        # Record login attempt
        login_record = LoginHistory(
            user_id=user.id if user else None,
            email_attempted=email,
            ip_address=ip_address,
            user_agent=user_agent,
            success=False,
        )
        
        if not user:
            login_record.failure_reason = "User not found"
            db.add(login_record)
            await db.commit()
            return None
        
        # Check if account is locked
        if user.is_locked():
            login_record.failure_reason = "Account locked"
            db.add(login_record)
            await db.commit()
            return None
        
        # Check if account is active
        if not user.is_active:
            login_record.failure_reason = "Account inactive"
            db.add(login_record)
            await db.commit()
            return None
        
        # Verify password
        if not self.verify_password(password, user.hashed_password):
            user.record_failed_login()
            login_record.failure_reason = "Invalid password"
            db.add(login_record)
            await db.commit()
            return None
        
        # Successful authentication
        user.record_successful_login(ip_address)
        login_record.success = True
        login_record.failure_reason = None
        
        db.add(login_record)
        await db.commit()
        
        return user
    
    async def change_password(
        self,
        db: AsyncSession,
        *,
        user: User,
        current_password: str,
        new_password: str,
    ) -> bool:
        """
        Change user's password.
        
        Requires verification of current password.
        """
        if not self.verify_password(current_password, user.hashed_password):
            return False
        
        user.hashed_password = self.hash_password(new_password)
        user.password_changed_at = datetime.datetime.now(datetime.timezone.utc)
        
        await db.commit()
        return True
    
    async def reset_password(
        self,
        db: AsyncSession,
        *,
        user: User,
        new_password: str,
    ):
        """
        Reset user's password (admin action).
        """
        user.hashed_password = self.hash_password(new_password)
        user.password_changed_at = datetime.datetime.now(datetime.timezone.utc)
        user.password_reset_token = None
        user.password_reset_expires = None
        
        await db.commit()
    
    async def get_user_permissions(
        self,
        db: AsyncSession,
        user: User,
    ) -> List[Permission]:
        """
        Get all permissions for a user across all their roles.
        """
        permissions = set()
        for role in user.roles:
            for permission in role.permissions:
                permissions.add(permission)
        return list(permissions)
    
    async def has_permission(
        self,
        db: AsyncSession,
        user: User,
        resource: str,
        action: str,
    ) -> bool:
        """
        Check if user has a specific permission.
        """
        if user.is_superuser:
            return True
        
        permissions = await self.get_user_permissions(db, user)
        for perm in permissions:
            if perm.resource == resource and perm.action.value == action:
                return True
        return False


# Singleton instance
user_service = UserService()
