"""
Account Management API
======================
CRUD endpoints for multi-account user management.

Access Control:
- POST /accounts: SuperUser/Admin only
- GET /accounts: Staff with permission
- GET /accounts/{id}: Authorized users
- PUT /accounts/{id}: SuperUser/Admin
- DELETE /accounts/{id}: SuperUser only
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, EmailStr, Field, field_validator
from datetime import datetime
import enum

from app.database.session import get_db
from app.middleware.security import get_current_user
from app.models.user.model import User, UserRole, AccountType, UserStatus
from app.services.account_service import (
    get_account_service,
    AccountValidationError,
    AccountNotFoundError
)

router = APIRouter()


# =============================================================================
# SCHEMAS
# =============================================================================

class AccountBase(BaseModel):
    """Base account fields."""
    email: EmailStr
    full_name: str = Field(..., min_length=2, max_length=255)


class AccountCreateStaff(AccountBase):
    """Schema for creating a staff account."""
    password: str = Field(..., min_length=8)
    department: str = Field(..., min_length=2, max_length=100)
    role: UserRole = UserRole.DEVELOPER
    
    @field_validator('password')
    @classmethod
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters')
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not any(c.islower() for c in v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain at least one digit')
        return v


class AccountCreateClient(AccountBase):
    """Schema for creating a client account."""
    password: str = Field(..., min_length=8)
    company_name: str = Field(..., min_length=2, max_length=255)
    company_id: Optional[int] = None
    project_ids: List[int] = Field(..., min_length=1)
    
    @field_validator('password')
    @classmethod
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters')
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not any(c.islower() for c in v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain at least one digit')
        return v


class AccountUpdateStaff(BaseModel):
    """Schema for updating staff account."""
    full_name: Optional[str] = Field(None, min_length=2, max_length=255)
    department: Optional[str] = Field(None, min_length=2, max_length=100)
    role: Optional[UserRole] = None
    is_active: Optional[bool] = None


class AccountUpdateClient(BaseModel):
    """Schema for updating client account."""
    full_name: Optional[str] = Field(None, min_length=2, max_length=255)
    company_name: Optional[str] = Field(None, min_length=2, max_length=255)
    project_ids: Optional[List[int]] = None
    is_active: Optional[bool] = None


class AccountResponse(BaseModel):
    """Account response schema."""
    id: int
    email: str
    full_name: str
    account_type: AccountType
    status: UserStatus
    is_active: bool
    role: UserRole
    department: Optional[str] = None
    company_name: Optional[str] = None
    company_id: Optional[int] = None
    avatar_url: Optional[str] = None
    created_at: Optional[datetime] = None
    last_login_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class AccountListResponse(BaseModel):
    """Account list response schema."""
    accounts: List[AccountResponse]
    total: int
    page: int
    page_size: int
    has_more: bool


class ProjectAssignmentRequest(BaseModel):
    """Schema for project assignment."""
    project_ids: List[int] = Field(..., min_length=1)
    access_level: str = "VIEW"


# =============================================================================
# ENDPOINTS
# =============================================================================

@router.post("/staff", response_model=AccountResponse, status_code=status.HTTP_201_CREATED)
async def create_staff_account(
    account_data: AccountCreateStaff,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Create a new staff account.
    
    Access: SuperUser or Admin only
    """
    # Authorization check
    if not (current_user.is_superuser or current_user.role in [UserRole.SUPER_ADMIN, UserRole.ADMIN]):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only SuperUser or Admin can create staff accounts"
        )
    
    try:
        service = get_account_service(db)
        user = await service.create_account(
            email=account_data.email,
            password=account_data.password,
            full_name=account_data.full_name,
            account_type=AccountType.STAFF,
            created_by_id=current_user.id,
            department=account_data.department,
            role=account_data.role,
        )
        return user
    except AccountValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/client", response_model=AccountResponse, status_code=status.HTTP_201_CREATED)
async def create_client_account(
    account_data: AccountCreateClient,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Create a new client account.
    
    Access: SuperUser or Admin only
    """
    # Authorization check
    if not (current_user.is_superuser or current_user.role in [UserRole.SUPER_ADMIN, UserRole.ADMIN]):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only SuperUser or Admin can create client accounts"
        )
    
    try:
        service = get_account_service(db)
        user = await service.create_account(
            email=account_data.email,
            password=account_data.password,
            full_name=account_data.full_name,
            account_type=AccountType.CLIENT,
            created_by_id=current_user.id,
            company_name=account_data.company_name,
            company_id=account_data.company_id,
            project_ids=account_data.project_ids,
        )
        return user
    except AccountValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("", response_model=AccountListResponse)
async def list_accounts(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    account_type: Optional[AccountType] = None,
    search: Optional[str] = None,
    is_active: Optional[bool] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    List all accounts with filtering.
    
    Access:
    - SuperUser/Admin: Can see all accounts
    - Staff: Can see staff and clients
    - Client: Can only see own account
    """
    # Clients can only access their own data
    if current_user.account_type == AccountType.CLIENT:
        return AccountListResponse(
            accounts=[AccountResponse.model_validate(current_user)],
            total=1,
            page=1,
            page_size=page_size,
            has_more=False
        )
    
    service = get_account_service(db)
    result = await service.list_accounts(
        page=page,
        page_size=page_size,
        account_type=account_type,
        search=search,
        is_active=is_active,
        requesting_user=current_user,
    )
    
    return AccountListResponse(
        accounts=[AccountResponse.model_validate(acc) for acc in result["accounts"]],
        total=result["total"],
        page=result["page"],
        page_size=result["page_size"],
        has_more=result["has_more"],
    )


@router.get("/{account_id}", response_model=AccountResponse)
async def get_account(
    account_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get a specific account by ID.
    
    Access:
    - SuperUser/Admin: Can view any account
    - Staff: Can view staff and clients
    - Client: Can only view own account
    """
    # Clients can only view their own data
    if current_user.account_type == AccountType.CLIENT and current_user.id != account_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only view your own account"
        )
    
    try:
        service = get_account_service(db)
        user = await service.get_account(account_id)
        return user
    except AccountNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Account {account_id} not found"
        )


@router.put("/{account_id}/staff", response_model=AccountResponse)
async def update_staff_account(
    account_id: int,
    update_data: AccountUpdateStaff,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Update a staff account.
    
    Access: SuperUser or Admin only
    """
    if not (current_user.is_superuser or current_user.role in [UserRole.SUPER_ADMIN, UserRole.ADMIN]):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only SuperUser or Admin can update accounts"
        )
    
    try:
        service = get_account_service(db)
        user = await service.update_account(
            account_id,
            full_name=update_data.full_name,
            department=update_data.department,
            role=update_data.role,
            is_active=update_data.is_active,
        )
        return user
    except AccountNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Account {account_id} not found"
        )
    except AccountValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.put("/{account_id}/client", response_model=AccountResponse)
async def update_client_account(
    account_id: int,
    update_data: AccountUpdateClient,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Update a client account.
    
    Access: SuperUser or Admin only
    """
    if not (current_user.is_superuser or current_user.role in [UserRole.SUPER_ADMIN, UserRole.ADMIN]):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only SuperUser or Admin can update accounts"
        )
    
    try:
        service = get_account_service(db)
        user = await service.update_account(
            account_id,
            full_name=update_data.full_name,
            company_name=update_data.company_name,
            project_ids=update_data.project_ids,
            is_active=update_data.is_active,
        )
        return user
    except AccountNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Account {account_id} not found"
        )
    except AccountValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.delete("/{account_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_account(
    account_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Delete an account.
    
    Access: SuperUser only
    """
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only SuperUser can delete accounts"
        )
    
    try:
        service = get_account_service(db)
        await service.delete_account(account_id)
    except AccountNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Account {account_id} not found"
        )
    except AccountValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/{account_id}/projects", status_code=status.HTTP_204_NO_CONTENT)
async def assign_projects_to_client(
    account_id: int,
    assignment: ProjectAssignmentRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Assign projects to a client account.
    
    Access: SuperUser or Admin only
    """
    if not (current_user.is_superuser or current_user.role in [UserRole.SUPER_ADMIN, UserRole.ADMIN]):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only SuperUser or Admin can assign projects"
        )
    
    try:
        service = get_account_service(db)
        await service.assign_projects_to_client(
            account_id,
            assignment.project_ids,
            assigned_by_id=current_user.id,
            access_level=assignment.access_level
        )
    except AccountNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Account {account_id} not found"
        )
    except AccountValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.delete("/{account_id}/projects/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_project_from_client(
    account_id: int,
    project_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Remove a project from a client account.
    
    Access: SuperUser or Admin only
    """
    if not (current_user.is_superuser or current_user.role in [UserRole.SUPER_ADMIN, UserRole.ADMIN]):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only SuperUser or Admin can remove projects"
        )
    
    try:
        service = get_account_service(db)
        await service.remove_project_from_client(account_id, project_id)
    except AccountNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Account {account_id} not found"
        )
    except AccountValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/me", response_model=AccountResponse)
async def get_current_account(
    current_user: User = Depends(get_current_user),
):
    """
    Get the current user's account details.
    """
    return current_user
