"""
WorkSynapse Create Admin Command
================================
Command to create admin/superuser accounts with proper security.

Features:
- Secure password handling (no logging of plain text)
- Idempotent operation (skips if exists)
- Role assignment via RBAC tables
- Input validation
- Transaction-safe creation

Usage:
    python manage.py create_admin --email admin@worksynapse.com --username admin --password StrongPass123!
    python manage.py create_admin --email super@worksynapse.com --username superadmin --password StrongPass123! --superuser
"""

import re
from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.commands.base_command import BaseCommand
from app.services.user import user_service
from app.models.user.model import User, Role, UserRole, UserStatus


class CreateAdminCommand(BaseCommand):
    """
    Command to create a new admin or superuser account.
    
    This command:
    1. Validates email and username uniqueness
    2. Validates password strength
    3. Creates user with hashed password
    4. Assigns appropriate role (Admin or SuperAdmin)
    5. Sets user as active and verified
    
    Security:
    - Passwords are never logged
    - Passwords are hashed using bcrypt/argon2
    - Validation follows OWASP guidelines
    """
    
    name = "create_admin"
    description = "Create a new admin or superuser account"
    
    # Password requirements
    MIN_PASSWORD_LENGTH = 8
    PASSWORD_PATTERN = r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[!@#$%^&*(),.?":{}|<>]).{8,}$'
    
    async def validate(
        self,
        email: str = None,
        username: str = None,
        password: str = None,
        **kwargs
    ) -> bool:
        """
        Validate input parameters before execution.
        """
        errors = []
        
        # Email validation
        if not email:
            errors.append("Email is required")
        elif not self._is_valid_email(email):
            errors.append("Invalid email format")
        
        # Username validation
        if not username:
            errors.append("Username is required")
        elif len(username) < 3:
            errors.append("Username must be at least 3 characters")
        elif not re.match(r'^[a-zA-Z0-9_-]+$', username):
            errors.append("Username can only contain letters, numbers, underscores, and hyphens")
        
        # Password validation
        if not password:
            errors.append("Password is required")
        elif len(password) < self.MIN_PASSWORD_LENGTH:
            errors.append(f"Password must be at least {self.MIN_PASSWORD_LENGTH} characters")
        elif not re.match(self.PASSWORD_PATTERN, password):
            errors.append("Password must contain uppercase, lowercase, digit, and special character")
        
        if errors:
            self.output.header("Validation Errors")
            for error in errors:
                self.output.error(error)
            return False
        
        return True
    
    def _is_valid_email(self, email: str) -> bool:
        """Validate email format."""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email))
    
    async def execute(
        self,
        db: AsyncSession,
        email: str,
        username: str,
        password: str,
        full_name: str = "System Administrator",
        superuser: bool = False,
    ) -> Optional[User]:
        """
        Create the admin user with proper role assignment.
        
        Args:
            db: Database session
            email: User's email address
            username: User's username
            password: Plain text password (will be hashed)
            full_name: User's display name
            superuser: If True, creates a superuser with full system access
        
        Returns:
            Created User object, or None if user already exists
        """
        self.output.header(f"Creating {'Super Admin' if superuser else 'Admin'} User")
        
        # Log operation (without password)
        self.log_secure(
            "Creating admin user",
            email=email,
            username=username,
            password="***",  # Never log passwords
            superuser=superuser
        )
        
        # Check if user exists by email
        existing_email = await user_service.get_by_email(db, email=email)
        if existing_email:
            self.output.warning(f"User with email '{email}' already exists")
            self.output.info("Skipping creation (idempotent operation)")
            return None
        
        # Check if username exists
        existing_username = await user_service.get_by_username(db, username=username)
        if existing_username:
            self.output.warning(f"Username '{username}' is already taken")
            self.output.info("Skipping creation (idempotent operation)")
            return None
        
        # Determine role
        role_enum = UserRole.SUPER_ADMIN if superuser else UserRole.ADMIN
        role_name = role_enum.value
        
        # Fetch or create role
        stmt = select(Role).where(Role.name == role_name)
        result = await db.execute(stmt)
        role = result.scalars().first()
        
        if not role:
            self.output.info(f"Role '{role_name}' not found. Creating system role...")
            role = Role(
                name=role_name,
                description=f"System {role_name.replace('_', ' ').title()} Role",
                is_system=True,
                is_active=True
            )
            db.add(role)
            await db.flush()  # Get the ID without committing
            self.output.success(f"Created role: {role_name}")
        
        # Create user with hashed password
        hashed_password = user_service.hash_password(password)
        
        new_user = User(
            email=email.lower().strip(),
            username=username.lower().strip(),
            full_name=full_name.strip(),
            hashed_password=hashed_password,
            is_active=True,
            is_superuser=superuser,
            status=UserStatus.ACTIVE,
            email_verified=True,
            role=role_enum,  # Legacy field for backwards compatibility
        )
        
        # Assign role via many-to-many relationship
        new_user.roles.append(role)
        
        db.add(new_user)
        await db.flush()
        await db.refresh(new_user)
        
        # Output success details
        self.output.divider()
        self.output.success("User created successfully!")
        self.output.divider()
        self.output.table_row("User ID", str(new_user.id))
        self.output.table_row("Email", new_user.email)
        self.output.table_row("Username", new_user.username)
        self.output.table_row("Full Name", new_user.full_name)
        self.output.table_row("Role", role_name)
        self.output.table_row("Superuser", "Yes" if superuser else "No")
        self.output.table_row("Status", new_user.status.value)
        self.output.divider()
        
        self.logger.info(f"Successfully created user: {username} ({email})")
        
        return new_user
