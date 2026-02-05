"""
WorkSynapse Project Management Models
=====================================
Complete project management with Kanban boards, sprints, and team collaboration.

Features:
- Project lifecycle management
- Kanban boards with columns
- Sprint planning
- Member permissions
- Task dependencies
"""
from typing import List, Optional
from sqlalchemy import (
    String, Boolean, Enum, ForeignKey, Text, Integer, 
    DateTime, Index, UniqueConstraint, CheckConstraint,
    JSON, Table, Column, Float
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base, AuditMixin
import enum
import datetime


# =============================================================================
# ENUMS
# =============================================================================

class ProjectStatus(str, enum.Enum):
    """Project lifecycle status."""
    PLANNING = "PLANNING"
    ACTIVE = "ACTIVE"
    ON_HOLD = "ON_HOLD"
    COMPLETED = "COMPLETED"
    ARCHIVED = "ARCHIVED"
    CANCELLED = "CANCELLED"


class ProjectVisibility(str, enum.Enum):
    """Project visibility settings."""
    PRIVATE = "PRIVATE"
    TEAM = "TEAM"
    ORGANIZATION = "ORGANIZATION"
    PUBLIC = "PUBLIC"


class MemberRole(str, enum.Enum):
    """Member role within a project."""
    OWNER = "OWNER"
    ADMIN = "ADMIN"
    MEMBER = "MEMBER"
    VIEWER = "VIEWER"
    GUEST = "GUEST"


class SprintStatus(str, enum.Enum):
    """Sprint status."""
    PLANNING = "PLANNING"
    ACTIVE = "ACTIVE"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"


# =============================================================================
# PROJECT MODEL
# =============================================================================

class Project(Base, AuditMixin):
    """
    Project container for tasks and collaboration.
    
    Features:
    - Multiple boards per project
    - Team member management
    - Sprint support
    - Milestone tracking
    """
    __tablename__ = "projects"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    
    # Basic info
    name: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    key: Mapped[str] = mapped_column(String(10), unique=True, index=True, nullable=False)  # e.g., "PRJ", "WS"
    
    # Status & visibility
    status: Mapped[ProjectStatus] = mapped_column(
        Enum(ProjectStatus),
        default=ProjectStatus.PLANNING
    )
    visibility: Mapped[ProjectVisibility] = mapped_column(
        Enum(ProjectVisibility),
        default=ProjectVisibility.PRIVATE
    )
    
    # Ownership
    owner_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        index=True,
        nullable=False
    )
    
    # Dates
    start_date: Mapped[Optional[datetime.date]] = mapped_column(nullable=True)
    target_end_date: Mapped[Optional[datetime.date]] = mapped_column(nullable=True)
    actual_end_date: Mapped[Optional[datetime.date]] = mapped_column(nullable=True)
    
    # Settings
    settings: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    color: Mapped[Optional[str]] = mapped_column(String(7), nullable=True)  # Hex color
    icon: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    
    # Task counter for auto-numbering (e.g., PRJ-001)
    task_counter: Mapped[int] = mapped_column(Integer, default=0)
    
    # Relationships
    owner = relationship("User", back_populates="projects", foreign_keys=[owner_id])
    members: Mapped[List["ProjectMember"]] = relationship(
        back_populates="project",
        cascade="all, delete-orphan"
    )
    boards: Mapped[List["Board"]] = relationship(
        back_populates="project",
        cascade="all, delete-orphan"
    )
    sprints: Mapped[List["Sprint"]] = relationship(
        back_populates="project",
        cascade="all, delete-orphan"
    )
    milestones: Mapped[List["Milestone"]] = relationship(
        back_populates="project",
        cascade="all, delete-orphan"
    )
    tasks = relationship("Task", back_populates="project")
    notes = relationship("Note", back_populates="project")
    channels = relationship("Channel", back_populates="project")
    
    # Client access - assigned client users
    assigned_users = relationship(
        "User",
        secondary="user_project_assignments",
        back_populates="assigned_projects"
    )
    
    __table_args__ = (
        CheckConstraint("length(name) >= 1", name="check_project_name_length"),
        CheckConstraint("length(key) >= 2 AND length(key) <= 10", name="check_project_key_length"),
        CheckConstraint(
            "target_end_date IS NULL OR start_date IS NULL OR target_end_date >= start_date",
            name="check_project_dates"
        ),
        Index("ix_projects_owner_status", "owner_id", "status"),
    )
    
    def get_next_task_number(self) -> str:
        """Generate next task number (e.g., PRJ-001)."""
        self.task_counter += 1
        return f"{self.key}-{self.task_counter:03d}"


# =============================================================================
# PROJECT MEMBER MODEL
# =============================================================================

class ProjectMember(Base):
    """
    Project membership with role-based permissions.
    """
    __tablename__ = "project_members"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    
    # References
    project_id: Mapped[int] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"),
        index=True,
        nullable=False
    )
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
        nullable=False
    )
    
    # Role in project
    role: Mapped[MemberRole] = mapped_column(
        Enum(MemberRole),
        default=MemberRole.MEMBER
    )
    
    # Tracking
    joined_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        server_default="now()"
    )
    invited_by_user_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("users.id"),
        nullable=True
    )
    
    # Notification preferences
    notifications_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    
    # Relationships
    project: Mapped["Project"] = relationship(back_populates="members")
    user = relationship("User", foreign_keys=[user_id])
    invited_by = relationship("User", foreign_keys=[invited_by_user_id])
    
    __table_args__ = (
        UniqueConstraint("project_id", "user_id", name="uq_project_member"),
        Index("ix_project_members_user", "user_id"),
    )


# =============================================================================
# BOARD MODEL
# =============================================================================

class Board(Base):
    """
    Kanban board within a project.
    
    Each project can have multiple boards (e.g., Development, Design, Marketing).
    """
    __tablename__ = "boards"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    
    # Basic info
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Project reference
    project_id: Mapped[int] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"),
        index=True,
        nullable=False
    )
    
    # Ordering
    position: Mapped[int] = mapped_column(Integer, default=0)
    
    # Settings
    is_default: Mapped[bool] = mapped_column(Boolean, default=False)
    settings: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    
    # Relationships
    project: Mapped["Project"] = relationship(back_populates="boards")
    columns: Mapped[List["BoardColumn"]] = relationship(
        back_populates="board",
        cascade="all, delete-orphan",
        order_by="BoardColumn.position"
    )
    
    __table_args__ = (
        Index("ix_boards_project_default", "project_id", "is_default"),
    )


# =============================================================================
# BOARD COLUMN MODEL
# =============================================================================

class BoardColumn(Base):
    """
    Column in a Kanban board.
    
    Examples: To Do, In Progress, Review, Done
    """
    __tablename__ = "board_columns"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    
    # Basic info
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    
    # Board reference
    board_id: Mapped[int] = mapped_column(
        ForeignKey("boards.id", ondelete="CASCADE"),
        index=True,
        nullable=False
    )
    
    # Ordering and display
    position: Mapped[int] = mapped_column(Integer, default=0)
    color: Mapped[Optional[str]] = mapped_column(String(7), nullable=True)  # Hex color
    
    # WIP limit (Work In Progress)
    wip_limit: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    
    # Status mapping
    is_done_column: Mapped[bool] = mapped_column(Boolean, default=False)
    is_initial_column: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # Relationships
    board: Mapped["Board"] = relationship(back_populates="columns")
    tasks = relationship("Task", back_populates="column")
    
    __table_args__ = (
        CheckConstraint("wip_limit IS NULL OR wip_limit > 0", name="check_wip_limit_positive"),
        Index("ix_board_columns_board_position", "board_id", "position"),
    )


# =============================================================================
# SPRINT MODEL
# =============================================================================

class Sprint(Base):
    """
    Sprint for agile project management.
    """
    __tablename__ = "sprints"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    
    # Basic info
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    goal: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Project reference
    project_id: Mapped[int] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"),
        index=True,
        nullable=False
    )
    
    # Sprint number within project
    sprint_number: Mapped[int] = mapped_column(Integer, nullable=False)
    
    # Status
    status: Mapped[SprintStatus] = mapped_column(
        Enum(SprintStatus),
        default=SprintStatus.PLANNING
    )
    
    # Dates
    start_date: Mapped[Optional[datetime.date]] = mapped_column(nullable=True)
    end_date: Mapped[Optional[datetime.date]] = mapped_column(nullable=True)
    
    # Metrics
    planned_velocity: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    actual_velocity: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    
    # Relationships
    project: Mapped["Project"] = relationship(back_populates="sprints")
    tasks = relationship("Task", back_populates="sprint")
    
    __table_args__ = (
        UniqueConstraint("project_id", "sprint_number", name="uq_sprint_number"),
        CheckConstraint(
            "end_date IS NULL OR start_date IS NULL OR end_date >= start_date",
            name="check_sprint_dates"
        ),
        Index("ix_sprints_project_status", "project_id", "status"),
    )


# =============================================================================
# MILESTONE MODEL
# =============================================================================

class Milestone(Base):
    """
    Project milestone for tracking major deliverables.
    """
    __tablename__ = "milestones"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    
    # Basic info
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Project reference
    project_id: Mapped[int] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"),
        index=True,
        nullable=False
    )
    
    # Status
    completed: Mapped[bool] = mapped_column(Boolean, default=False)
    completed_at: Mapped[Optional[datetime.datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )
    
    # Target date
    due_date: Mapped[Optional[datetime.date]] = mapped_column(nullable=True)
    
    # Relationships
    project: Mapped["Project"] = relationship(back_populates="milestones")
    tasks = relationship("Task", back_populates="milestone")
    
    __table_args__ = (
        Index("ix_milestones_project_due", "project_id", "due_date"),
    )
