"""
WorkSynapse User & Authentication Models
=========================================
Secure user management with RBAC, sessions, and MFA support.

Security Features:
- Bcrypt password hashing
- Role-based access control (RBAC)
- Fine-grained permissions
- Session tracking with device info
- Login attempt logging
- MFA support (TOTP)
"""
from typing import List, Optional
from sqlalchemy import (
    String, Boolean, Enum, ForeignKey, Text, Integer, 
    DateTime, Index, UniqueConstraint, CheckConstraint,
    JSON, Table, Column
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base, AuditMixin
import enum
import datetime


# =============================================================================
# ENUMS
# =============================================================================

class UserRole(str, enum.Enum):
    """System-wide user roles."""
    SUPER_ADMIN = "SUPER_ADMIN"
    ADMIN = "ADMIN"
    MANAGER = "MANAGER"
    TEAM_LEAD = "TEAM_LEAD"
    DEVELOPER = "DEVELOPER"
    VIEWER = "VIEWER"
    GUEST = "GUEST"


class UserStatus(str, enum.Enum):
    """User account status."""
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    SUSPENDED = "SUSPENDED"
    PENDING_VERIFICATION = "PENDING_VERIFICATION"
    LOCKED = "LOCKED"


class PermissionAction(str, enum.Enum):
    """Permission actions for RBAC."""
    CREATE = "CREATE"
    READ = "READ"
    UPDATE = "UPDATE"
    DELETE = "DELETE"
    MANAGE = "MANAGE"  # Full control
    EXECUTE = "EXECUTE"  # For AI agents
    EXPORT = "EXPORT"
    APPROVE = "APPROVE"


# =============================================================================
# ASSOCIATION TABLES
# =============================================================================

# Many-to-many: Users <-> Roles
user_roles = Table(
    "user_roles",
    Base.metadata,
    Column("user_id", Integer, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
    Column("role_id", Integer, ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True),
    Column("assigned_at", DateTime(timezone=True), server_default="now()"),
    Column("assigned_by_user_id", Integer, nullable=True),
)

# Many-to-many: Roles <-> Permissions
role_permissions = Table(
    "role_permissions",
    Base.metadata,
    Column("role_id", Integer, ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True),
    Column("permission_id", Integer, ForeignKey("permissions.id", ondelete="CASCADE"), primary_key=True),
)


# =============================================================================
# USER MODEL
# =============================================================================

class User(Base):
    """
    System user with security features.
    
    Security:
    - Password stored as bcrypt hash
    - Email validation enforced
    - Failed login tracking
    - Account lockout support
    """
    __tablename__ = "users"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    
    # Identity
    email: Mapped[str] = mapped_column(
        String(255), 
        unique=True, 
        index=True,
        nullable=False
    )
    username: Mapped[Optional[str]] = mapped_column(
        String(50),
        unique=True,
        index=True,
        nullable=True
    )
    full_name: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    
    # Authentication
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    password_changed_at: Mapped[Optional[datetime.datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )
    
    # MFA Support
    mfa_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    mfa_secret: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)  # Encrypted TOTP secret
    
    # Status & Security
    status: Mapped[UserStatus] = mapped_column(
        Enum(UserStatus), 
        default=UserStatus.PENDING_VERIFICATION
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_superuser: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # Legacy role field (keep for backwards compatibility)
    role: Mapped[UserRole] = mapped_column(
        Enum(UserRole), 
        default=UserRole.DEVELOPER
    )
    
    # Security Tracking
    failed_login_attempts: Mapped[int] = mapped_column(Integer, default=0)
    locked_until: Mapped[Optional[datetime.datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )
    last_login_at: Mapped[Optional[datetime.datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )
    last_login_ip: Mapped[Optional[str]] = mapped_column(String(45), nullable=True)
    
    # Profile
    avatar_url: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    timezone: Mapped[str] = mapped_column(String(50), default="UTC")
    locale: Mapped[str] = mapped_column(String(10), default="en")
    
    # Email verification
    email_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    email_verification_token: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    
    # Password reset
    password_reset_token: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    password_reset_expires: Mapped[Optional[datetime.datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )
    
    # Relationships
    roles: Mapped[List["Role"]] = relationship(
        "Role",
        secondary=user_roles,
        back_populates="users",
        lazy="selectin"
    )
    sessions: Mapped[List["Session"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    login_history: Mapped[List["LoginHistory"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    
    # Business relationships (defined via string reference)
    projects = relationship("Project", back_populates="owner", foreign_keys="[Project.owner_id]")
    assigned_tasks = relationship("Task", back_populates="assignee", foreign_keys="[Task.assignee_id]")
    worklogs = relationship("WorkLog", back_populates="user")
    messages = relationship("Message", back_populates="sender")
    notes = relationship("Note", back_populates="owner", foreign_keys="[Note.owner_id]")
    
    # LLM/AI relationships (User-created agents and API keys)
    llm_api_keys = relationship(
        "LLMApiKey",
        back_populates="user",
        foreign_keys="[LLMApiKey.user_id]",
        cascade="all, delete-orphan"
    )
    ai_agents = relationship(
        "UserAIAgent",
        back_populates="user",
        foreign_keys="[UserAIAgent.user_id]",
        cascade="all, delete-orphan"
    )
    
    # Constraints
    __table_args__ = (
        CheckConstraint("length(email) >= 5", name="check_email_length"),
        CheckConstraint("failed_login_attempts >= 0", name="check_failed_attempts_positive"),
        Index("ix_users_email_active", "email", "is_active"),
    )
    
    def is_locked(self) -> bool:
        """Check if account is locked."""
        if self.locked_until is None:
            return False
        return datetime.datetime.now(datetime.timezone.utc) < self.locked_until
    
    def record_failed_login(self, max_attempts: int = 5, lockout_minutes: int = 30):
        """Record failed login attempt and potentially lock account."""
        self.failed_login_attempts += 1
        if self.failed_login_attempts >= max_attempts:
            self.locked_until = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(minutes=lockout_minutes)
    
    def record_successful_login(self, ip_address: str):
        """Record successful login."""
        self.failed_login_attempts = 0
        self.locked_until = None
        self.last_login_at = datetime.datetime.now(datetime.timezone.utc)
        self.last_login_ip = ip_address
    
    def has_permission(self, resource: str, action: PermissionAction) -> bool:
        """Check if user has specific permission."""
        if self.is_superuser:
            return True
        for role in self.roles:
            for permission in role.permissions:
                if permission.resource == resource and permission.action == action:
                    return True
        return False


# =============================================================================
# ROLE MODEL
# =============================================================================

class Role(Base):
    """
    System role for RBAC.
    
    Roles group permissions and can be assigned to users.
    """
    __tablename__ = "roles"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # System role cannot be deleted
    is_system: Mapped[bool] = mapped_column(Boolean, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    
    # Role hierarchy (for inheritance)
    parent_role_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("roles.id"),
        nullable=True
    )
    
    # Relationships
    users: Mapped[List["User"]] = relationship(
        "User",
        secondary=user_roles,
        back_populates="roles"
    )
    permissions: Mapped[List["Permission"]] = relationship(
        secondary=role_permissions,
        back_populates="roles",
        lazy="selectin"
    )
    parent_role = relationship(
        "Role",
        remote_side="Role.id",
        backref="child_roles",
        foreign_keys=[parent_role_id]
    )
    
    __table_args__ = (
        CheckConstraint("length(name) >= 2", name="check_role_name_length"),
    )


# =============================================================================
# PERMISSION MODEL
# =============================================================================

class Permission(Base):
    """
    Fine-grained permission for RBAC.
    
    Permissions define what actions can be performed on which resources.
    """
    __tablename__ = "permissions"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    
    # Permission definition
    resource: Mapped[str] = mapped_column(String(100), index=True, nullable=False)  # e.g., "projects", "tasks", "agents"
    action: Mapped[PermissionAction] = mapped_column(Enum(PermissionAction), nullable=False)
    
    # Additional constraints
    conditions: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)  # e.g., {"own_only": true}
    
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    
    # Relationships
    roles: Mapped[List["Role"]] = relationship(
        secondary=role_permissions,
        back_populates="permissions"
    )
    
    __table_args__ = (
        UniqueConstraint("resource", "action", name="uq_permission_resource_action"),
        Index("ix_permissions_resource_action", "resource", "action"),
    )


# =============================================================================
# SESSION MODEL
# =============================================================================

class Session(Base):
    """
    User session tracking.
    
    Tracks active sessions with device info for security.
    """
    __tablename__ = "sessions"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    
    # Session identity
    session_token: Mapped[str] = mapped_column(
        String(512), 
        unique=True, 
        index=True,
        nullable=False
    )
    refresh_token: Mapped[Optional[str]] = mapped_column(String(512), unique=True, nullable=True)
    
    # User reference
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
        nullable=False
    )
    
    # Session metadata
    ip_address: Mapped[str] = mapped_column(String(45), nullable=False)
    user_agent: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    device_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)  # desktop, mobile, tablet
    device_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    browser: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    os: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    location: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)  # GeoIP lookup
    
    # Validity
    expires_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False
    )
    last_activity_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        server_default="now()"
    )
    
    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    revoked_at: Mapped[Optional[datetime.datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )
    revoked_reason: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    
    # Relationships
    user: Mapped["User"] = relationship(back_populates="sessions")
    
    __table_args__ = (
        Index("ix_sessions_user_active", "user_id", "is_active"),
        Index("ix_sessions_expires", "expires_at"),
    )
    
    def is_valid(self) -> bool:
        """Check if session is still valid."""
        if not self.is_active:
            return False
        if self.revoked_at is not None:
            return False
        return datetime.datetime.now(datetime.timezone.utc) < self.expires_at
    
    def revoke(self, reason: str = "Manual revocation"):
        """Revoke this session."""
        self.is_active = False
        self.revoked_at = datetime.datetime.now(datetime.timezone.utc)
        self.revoked_reason = reason


# =============================================================================
# LOGIN HISTORY MODEL
# =============================================================================

class LoginHistory(Base):
    """
    Login attempt history for security auditing.
    
    Tracks all login attempts (successful and failed).
    """
    __tablename__ = "login_history"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    
    # User (nullable for failed attempts with invalid email)
    user_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        index=True,
        nullable=True
    )
    email_attempted: Mapped[str] = mapped_column(String(255), nullable=False)
    
    # Attempt details
    success: Mapped[bool] = mapped_column(Boolean, nullable=False)
    failure_reason: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    
    # Request metadata
    ip_address: Mapped[str] = mapped_column(String(45), nullable=False)
    user_agent: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    location: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    
    # MFA info
    mfa_used: Mapped[bool] = mapped_column(Boolean, default=False)
    mfa_method: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)  # totp, sms, email
    
    # Relationships
    user: Mapped[Optional["User"]] = relationship(back_populates="login_history")
    
    __table_args__ = (
        Index("ix_login_history_user_created", "user_id", "created_at"),
        Index("ix_login_history_ip", "ip_address"),
        Index("ix_login_history_success", "success", "created_at"),
    )
