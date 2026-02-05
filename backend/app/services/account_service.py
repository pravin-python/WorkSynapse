"""
Account Service
===============
Service layer for multi-account user management.

Handles:
- Account creation (Staff/Client)
- Role assignment
- Project linking (for clients)
- Validation logic
"""
from typing import List, Optional, Any, Dict
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, and_, or_
from sqlalchemy.orm import joinedload
import logging

from app.models.user.model import (
    User, Role, UserStatus, UserRole, 
    AccountType, user_project_assignments
)
from app.models.project.model import Project
from app.core.security import get_password_hash, verify_password
from app.services.user import user_service

logger = logging.getLogger(__name__)


class AccountValidationError(Exception):
    """Raised when account validation fails."""
    pass


class AccountNotFoundError(Exception):
    """Raised when account is not found."""
    def __init__(self, account_id: int):
        self.account_id = account_id
        super().__init__(f"Account {account_id} not found")


class AccountService:
    """
    Service for managing user accounts.
    
    Supports:
    - SuperUser: Full system access
    - Staff: Internal team member
    - Client: External customer with limited access
    """
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def create_account(
        self,
        *,
        email: str,
        password: str,
        full_name: str,
        account_type: AccountType,
        created_by_id: Optional[int] = None,
        # Staff-specific fields
        department: Optional[str] = None,
        role: UserRole = UserRole.DEVELOPER,
        # Client-specific fields
        company_name: Optional[str] = None,
        company_id: Optional[int] = None,
        project_ids: Optional[List[int]] = None,
    ) -> User:
        """
        Create a new user account.
        
        Args:
            email: User email (must be unique)
            password: Plain text password (will be hashed)
            full_name: User's full name
            account_type: SUPERUSER, STAFF, or CLIENT
            created_by_id: ID of user creating this account
            department: Department (required for staff)
            role: User role (for staff)
            company_name: Company name (required for clients)
            company_id: Company ID for multi-tenant
            project_ids: Projects to assign (required for clients)
        
        Returns:
            Created User object
            
        Raises:
            AccountValidationError: If validation fails
        """
        # Validate email uniqueness
        existing = await self.db.execute(
            select(User).where(User.email == email.lower())
        )
        if existing.scalar_one_or_none():
            raise AccountValidationError(f"Email {email} already exists")
        
        # Account type specific validation
        if account_type == AccountType.STAFF:
            if not department:
                raise AccountValidationError("Department is required for staff accounts")
        
        elif account_type == AccountType.CLIENT:
            if not company_name:
                raise AccountValidationError("Company name is required for client accounts")
            if not project_ids or len(project_ids) == 0:
                raise AccountValidationError("At least one project must be assigned to client")
            
            # Verify projects exist
            projects = await self.db.execute(
                select(Project).where(Project.id.in_(project_ids))
            )
            found_projects = projects.scalars().all()
            if len(found_projects) != len(project_ids):
                raise AccountValidationError("One or more projects not found")
        
        # Validate password strength
        self._validate_password(password)
        
        # Create user
        user = User(
            email=email.lower(),
            full_name=full_name,
            hashed_password=get_password_hash(password),
            account_type=account_type,
            created_by_id=created_by_id,
            department=department,
            company_name=company_name,
            company_id=company_id,
            role=role if account_type == AccountType.STAFF else UserRole.GUEST,
            status=UserStatus.ACTIVE,
            is_active=True,
            is_superuser=account_type == AccountType.SUPERUSER,
        )
        
        self.db.add(user)
        await self.db.flush()  # Get user.id
        
        # Assign projects for clients
        if account_type == AccountType.CLIENT and project_ids:
            for project_id in project_ids:
                await self.db.execute(
                    user_project_assignments.insert().values(
                        user_id=user.id,
                        project_id=project_id,
                        assigned_by_user_id=created_by_id,
                        access_level="VIEW"
                    )
                )
        
        await self.db.commit()
        await self.db.refresh(user)
        
        logger.info(f"Created {account_type.value} account: {user.id} - {user.email}")
        return user
    
    async def get_account(self, account_id: int) -> User:
        """Get account by ID."""
        result = await self.db.execute(
            select(User)
            .options(joinedload(User.roles))
            .where(User.id == account_id)
        )
        user = result.unique().scalar_one_or_none()
        
        if not user:
            raise AccountNotFoundError(account_id)
        
        return user
    
    async def list_accounts(
        self,
        *,
        page: int = 1,
        page_size: int = 20,
        account_type: Optional[AccountType] = None,
        search: Optional[str] = None,
        is_active: Optional[bool] = None,
        requesting_user: Optional[User] = None,
    ) -> Dict[str, Any]:
        """
        List accounts with filtering and pagination.
        
        Args:
            page: Page number (1-indexed)
            page_size: Items per page
            account_type: Filter by account type
            search: Search in email and name
            is_active: Filter by active status
            requesting_user: User making the request (for access control)
        
        Returns:
            Dict with accounts, total, and pagination info
        """
        conditions = []
        
        # Account type filter
        if account_type:
            conditions.append(User.account_type == account_type)
        
        # Active filter
        if is_active is not None:
            conditions.append(User.is_active == is_active)
        
        # Search filter
        if search:
            search_term = f"%{search}%"
            conditions.append(
                or_(
                    User.email.ilike(search_term),
                    User.full_name.ilike(search_term),
                    User.company_name.ilike(search_term)
                )
            )
        
        # Access control: clients can only see their own data
        if requesting_user and requesting_user.account_type == AccountType.CLIENT:
            conditions.append(User.id == requesting_user.id)
        
        # Build query
        query = select(User).options(joinedload(User.roles))
        if conditions:
            query = query.where(and_(*conditions))
        query = query.order_by(User.created_at.desc())
        
        # Count total
        count_query = select(User.id)
        if conditions:
            count_query = count_query.where(and_(*conditions))
        count_result = await self.db.execute(count_query)
        total = len(count_result.all())
        
        # Paginate
        offset = (page - 1) * page_size
        query = query.offset(offset).limit(page_size)
        
        result = await self.db.execute(query)
        accounts = result.unique().scalars().all()
        
        return {
            "accounts": accounts,
            "total": total,
            "page": page,
            "page_size": page_size,
            "has_more": offset + len(accounts) < total,
        }
    
    async def update_account(
        self,
        account_id: int,
        *,
        full_name: Optional[str] = None,
        department: Optional[str] = None,
        company_name: Optional[str] = None,
        role: Optional[UserRole] = None,
        is_active: Optional[bool] = None,
        project_ids: Optional[List[int]] = None,
    ) -> User:
        """
        Update an account.
        
        Args:
            account_id: Account ID
            full_name: New full name
            department: New department (staff only)
            company_name: New company name (client only)
            role: New role (staff only)
            is_active: Active status
            project_ids: New project assignments (client only)
        
        Returns:
            Updated User object
        """
        user = await self.get_account(account_id)
        
        # Update basic fields
        if full_name is not None:
            user.full_name = full_name
        
        if is_active is not None:
            user.is_active = is_active
            user.status = UserStatus.ACTIVE if is_active else UserStatus.INACTIVE
        
        # Staff-specific updates
        if user.account_type == AccountType.STAFF:
            if department is not None:
                user.department = department
            if role is not None:
                user.role = role
        
        # Client-specific updates
        if user.account_type == AccountType.CLIENT:
            if company_name is not None:
                user.company_name = company_name
            
            if project_ids is not None:
                if len(project_ids) == 0:
                    raise AccountValidationError("Client must have at least one project")
                
                # Remove existing assignments
                await self.db.execute(
                    user_project_assignments.delete().where(
                        user_project_assignments.c.user_id == account_id
                    )
                )
                
                # Add new assignments
                for project_id in project_ids:
                    await self.db.execute(
                        user_project_assignments.insert().values(
                            user_id=account_id,
                            project_id=project_id,
                            access_level="VIEW"
                        )
                    )
        
        await self.db.commit()
        await self.db.refresh(user)
        
        logger.info(f"Updated account: {user.id}")
        return user
    
    async def delete_account(self, account_id: int) -> bool:
        """
        Delete an account.
        
        Only SuperUsers can delete accounts.
        """
        user = await self.get_account(account_id)
        
        # Prevent deleting superusers through this method
        if user.is_superuser:
            raise AccountValidationError("Cannot delete superuser account")
        
        await self.db.delete(user)
        await self.db.commit()
        
        logger.info(f"Deleted account: {account_id}")
        return True
    
    async def get_client_projects(self, client_id: int) -> List[Project]:
        """Get projects assigned to a client."""
        user = await self.get_account(client_id)
        
        if user.account_type != AccountType.CLIENT:
            raise AccountValidationError("User is not a client")
        
        result = await self.db.execute(
            select(Project)
            .join(
                user_project_assignments,
                Project.id == user_project_assignments.c.project_id
            )
            .where(user_project_assignments.c.user_id == client_id)
        )
        return result.scalars().all()
    
    async def assign_projects_to_client(
        self,
        client_id: int,
        project_ids: List[int],
        assigned_by_id: Optional[int] = None,
        access_level: str = "VIEW"
    ) -> None:
        """Assign additional projects to a client."""
        user = await self.get_account(client_id)
        
        if user.account_type != AccountType.CLIENT:
            raise AccountValidationError("User is not a client")
        
        for project_id in project_ids:
            await self.db.execute(
                user_project_assignments.insert().values(
                    user_id=client_id,
                    project_id=project_id,
                    assigned_by_user_id=assigned_by_id,
                    access_level=access_level
                )
            )
        
        await self.db.commit()
    
    async def remove_project_from_client(
        self,
        client_id: int,
        project_id: int
    ) -> None:
        """Remove a project from a client."""
        # Check if this is the only project
        result = await self.db.execute(
            select(user_project_assignments.c.project_id)
            .where(user_project_assignments.c.user_id == client_id)
        )
        project_count = len(result.all())
        
        if project_count <= 1:
            raise AccountValidationError("Cannot remove the only project from client")
        
        await self.db.execute(
            user_project_assignments.delete().where(
                and_(
                    user_project_assignments.c.user_id == client_id,
                    user_project_assignments.c.project_id == project_id
                )
            )
        )
        await self.db.commit()
    
    def _validate_password(self, password: str) -> None:
        """Validate password strength."""
        if len(password) < 8:
            raise AccountValidationError("Password must be at least 8 characters")
        
        if not any(c.isupper() for c in password):
            raise AccountValidationError("Password must contain at least one uppercase letter")
        
        if not any(c.islower() for c in password):
            raise AccountValidationError("Password must contain at least one lowercase letter")
        
        if not any(c.isdigit() for c in password):
            raise AccountValidationError("Password must contain at least one digit")


# Singleton instance
account_service: Optional[AccountService] = None

def get_account_service(db: AsyncSession) -> AccountService:
    """Get account service instance."""
    return AccountService(db)
