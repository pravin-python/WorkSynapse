"""
WorkSynapse Task Models
=======================
Complete task management with dependencies, labels, and time tracking.

Features:
- Task dependencies (blocking/blocked by)
- Labels and tags
- Estimates and time tracking
- Subtasks
- Attachments
- Comments
"""
from typing import List, Optional
from sqlalchemy import (
    String, Boolean, Enum, ForeignKey, Text, Integer, 
    DateTime, Index, UniqueConstraint, CheckConstraint,
    JSON, Table, Column, Float, Date
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base, AuditMixin
import enum
import datetime


# =============================================================================
# ENUMS
# =============================================================================

class TaskStatus(str, enum.Enum):
    """Task status."""
    BACKLOG = "BACKLOG"
    TODO = "TODO"
    IN_PROGRESS = "IN_PROGRESS"
    IN_REVIEW = "IN_REVIEW"
    TESTING = "TESTING"
    DONE = "DONE"
    CANCELLED = "CANCELLED"


class TaskPriority(str, enum.Enum):
    """Task priority levels."""
    LOWEST = "LOWEST"
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    HIGHEST = "HIGHEST"
    CRITICAL = "CRITICAL"


class TaskType(str, enum.Enum):
    """Task types."""
    TASK = "TASK"
    BUG = "BUG"
    FEATURE = "FEATURE"
    STORY = "STORY"
    EPIC = "EPIC"
    SUBTASK = "SUBTASK"
    IMPROVEMENT = "IMPROVEMENT"


class DependencyType(str, enum.Enum):
    """Task dependency types."""
    BLOCKS = "BLOCKS"           # This task blocks another
    BLOCKED_BY = "BLOCKED_BY"   # This task is blocked by another
    RELATES_TO = "RELATES_TO"   # Related tasks
    DUPLICATES = "DUPLICATES"   # Duplicate of another task
    PARENT_OF = "PARENT_OF"     # Parent task
    CHILD_OF = "CHILD_OF"       # Child/subtask


# =============================================================================
# ASSOCIATION TABLES
# =============================================================================

# Many-to-many: Tasks <-> Labels
task_labels = Table(
    "task_labels",
    Base.metadata,
    Column("task_id", Integer, ForeignKey("tasks.id", ondelete="CASCADE"), primary_key=True),
    Column("label_id", Integer, ForeignKey("labels.id", ondelete="CASCADE"), primary_key=True),
)

# Many-to-many: Tasks <-> Watchers
task_watchers = Table(
    "task_watchers",
    Base.metadata,
    Column("task_id", Integer, ForeignKey("tasks.id", ondelete="CASCADE"), primary_key=True),
    Column("user_id", Integer, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
    Column("added_at", DateTime(timezone=True), server_default="now()"),
)


# =============================================================================
# TASK MODEL
# =============================================================================

class Task(Base, AuditMixin):
    """
    Task with full tracking capabilities.
    
    Features:
    - Project and board association
    - Sprint assignment
    - Dependencies
    - Time tracking
    - Labels and watchers
    """
    __tablename__ = "tasks"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    
    # Identifier (e.g., PRJ-001)
    task_number: Mapped[str] = mapped_column(String(20), unique=True, index=True, nullable=False)
    
    # Basic info
    title: Mapped[str] = mapped_column(String(500), index=True, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Status and priority
    status: Mapped[TaskStatus] = mapped_column(
        Enum(TaskStatus),
        default=TaskStatus.BACKLOG,
        index=True
    )
    priority: Mapped[TaskPriority] = mapped_column(
        Enum(TaskPriority),
        default=TaskPriority.MEDIUM,
        index=True
    )
    task_type: Mapped[TaskType] = mapped_column(
        Enum(TaskType),
        default=TaskType.TASK
    )
    
    # Project association
    project_id: Mapped[int] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"),
        index=True,
        nullable=False
    )
    
    # Board and column (Kanban)
    column_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("board_columns.id", ondelete="SET NULL"),
        index=True,
        nullable=True
    )
    position_in_column: Mapped[int] = mapped_column(Integer, default=0)
    
    # Sprint assignment
    sprint_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("sprints.id", ondelete="SET NULL"),
        index=True,
        nullable=True
    )
    
    # Milestone
    milestone_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("milestones.id", ondelete="SET NULL"),
        index=True,
        nullable=True
    )
    
    # Assignment
    assignee_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        index=True,
        nullable=True
    )
    reporter_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True
    )
    
    # Parent task (for subtasks)
    parent_task_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("tasks.id", ondelete="CASCADE"),
        nullable=True
    )
    
    # Dates
    due_date: Mapped[Optional[datetime.date]] = mapped_column(Date, nullable=True)
    start_date: Mapped[Optional[datetime.date]] = mapped_column(Date, nullable=True)
    completed_at: Mapped[Optional[datetime.datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )
    
    # Time tracking (in minutes)
    estimated_minutes: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    logged_minutes: Mapped[int] = mapped_column(Integer, default=0)
    remaining_minutes: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    
    # Story points (for Agile)
    story_points: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    
    # Additional data
    custom_fields: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    
    # AI-generated flag
    is_ai_generated: Mapped[bool] = mapped_column(Boolean, default=False)
    ai_agent_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("agents.id", ondelete="SET NULL"),
        nullable=True
    )
    
    # Relationships
    project = relationship("Project", back_populates="tasks")
    column = relationship("BoardColumn", back_populates="tasks")
    sprint = relationship("Sprint", back_populates="tasks")
    milestone = relationship("Milestone", back_populates="tasks")
    assignee = relationship("User", back_populates="assigned_tasks", foreign_keys=[assignee_id])
    reporter = relationship("User", foreign_keys=[reporter_id])
    
    # Self-referential for subtasks
    parent_task = relationship("Task", remote_side=[id], backref="subtasks")
    
    # Many-to-many
    labels: Mapped[List["Label"]] = relationship(
        secondary=task_labels,
        back_populates="tasks"
    )
    watchers = relationship(
        "User",
        secondary=task_watchers,
        backref="watched_tasks"
    )
    
    # Related
    dependencies: Mapped[List["TaskDependency"]] = relationship(
        back_populates="task",
        foreign_keys="[TaskDependency.task_id]",
        cascade="all, delete-orphan"
    )
    comments: Mapped[List["TaskComment"]] = relationship(
        back_populates="task",
        cascade="all, delete-orphan"
    )
    attachments: Mapped[List["TaskAttachment"]] = relationship(
        back_populates="task",
        cascade="all, delete-orphan"
    )
    time_logs: Mapped[List["TimeLog"]] = relationship(
        back_populates="task",
        cascade="all, delete-orphan"
    )
    
    __table_args__ = (
        CheckConstraint("length(title) >= 1", name="check_task_title_length"),
        CheckConstraint(
            "due_date IS NULL OR start_date IS NULL OR due_date >= start_date",
            name="check_task_dates"
        ),
        CheckConstraint("estimated_minutes IS NULL OR estimated_minutes >= 0", name="check_estimated_positive"),
        CheckConstraint("logged_minutes >= 0", name="check_logged_positive"),
        CheckConstraint("story_points IS NULL OR story_points >= 0", name="check_story_points_positive"),
        Index("ix_tasks_project_status", "project_id", "status"),
        Index("ix_tasks_assignee_status", "assignee_id", "status"),
        Index("ix_tasks_sprint", "sprint_id"),
        Index("ix_tasks_due_date", "due_date"),
    )
    
    def complete(self):
        """Mark task as complete."""
        self.status = TaskStatus.DONE
        self.completed_at = datetime.datetime.now(datetime.timezone.utc)
    
    def log_time(self, minutes: int):
        """Log time worked on task."""
        self.logged_minutes += minutes
        if self.remaining_minutes is not None:
            self.remaining_minutes = max(0, self.remaining_minutes - minutes)


# =============================================================================
# TASK DEPENDENCY MODEL
# =============================================================================

class TaskDependency(Base):
    """
    Task dependencies (blocks, blocked by, relates to, etc.).
    """
    __tablename__ = "task_dependencies"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    
    # The task that has the dependency
    task_id: Mapped[int] = mapped_column(
        ForeignKey("tasks.id", ondelete="CASCADE"),
        index=True,
        nullable=False
    )
    
    # The related task
    related_task_id: Mapped[int] = mapped_column(
        ForeignKey("tasks.id", ondelete="CASCADE"),
        index=True,
        nullable=False
    )
    
    # Type of dependency
    dependency_type: Mapped[DependencyType] = mapped_column(
        Enum(DependencyType),
        nullable=False
    )
    
    # Optional notes
    notes: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    
    # Who created this dependency
    created_by_user_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("users.id"),
        nullable=True
    )
    
    # Relationships
    task: Mapped["Task"] = relationship(
        back_populates="dependencies",
        foreign_keys=[task_id]
    )
    related_task = relationship("Task", foreign_keys=[related_task_id])
    created_by = relationship("User")
    
    __table_args__ = (
        UniqueConstraint("task_id", "related_task_id", "dependency_type", name="uq_task_dependency"),
        CheckConstraint("task_id != related_task_id", name="check_not_self_dependency"),
    )


# =============================================================================
# LABEL MODEL
# =============================================================================

class Label(Base):
    """
    Labels/tags for tasks within a project.
    """
    __tablename__ = "labels"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    
    # Basic info
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    color: Mapped[str] = mapped_column(String(7), nullable=False)  # Hex color
    description: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    
    # Project scope (nullable = global label)
    project_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"),
        index=True,
        nullable=True
    )
    
    # Relationships
    tasks: Mapped[List["Task"]] = relationship(
        secondary=task_labels,
        back_populates="labels"
    )
    
    __table_args__ = (
        UniqueConstraint("project_id", "name", name="uq_label_project_name"),
    )


# =============================================================================
# TASK COMMENT MODEL
# =============================================================================

class TaskComment(Base, AuditMixin):
    """
    Comments on tasks.
    """
    __tablename__ = "task_comments"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    
    # Content
    content: Mapped[str] = mapped_column(Text, nullable=False)
    
    # Task reference
    task_id: Mapped[int] = mapped_column(
        ForeignKey("tasks.id", ondelete="CASCADE"),
        index=True,
        nullable=False
    )
    
    # Author
    author_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False
    )
    
    # Reply to another comment
    parent_comment_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("task_comments.id", ondelete="CASCADE"),
        nullable=True
    )
    
    # Edit tracking
    is_edited: Mapped[bool] = mapped_column(Boolean, default=False)
    edited_at: Mapped[Optional[datetime.datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )
    
    # Relationships
    task: Mapped["Task"] = relationship(back_populates="comments")
    author = relationship("User", foreign_keys=[author_id])
    parent_comment = relationship(
        "TaskComment",
        remote_side="TaskComment.id",
        backref="replies",
        foreign_keys=[parent_comment_id]
    )
    
    __table_args__ = (
        Index("ix_task_comments_task", "task_id", "created_at"),
    )


# =============================================================================
# TASK ATTACHMENT MODEL
# =============================================================================

class TaskAttachment(Base):
    """
    File attachments for tasks.
    """
    __tablename__ = "task_attachments"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    
    # File info
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    original_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    file_path: Mapped[str] = mapped_column(String(512), nullable=False)
    file_size: Mapped[int] = mapped_column(Integer, nullable=False)  # Bytes
    mime_type: Mapped[str] = mapped_column(String(100), nullable=False)
    
    # Task reference
    task_id: Mapped[int] = mapped_column(
        ForeignKey("tasks.id", ondelete="CASCADE"),
        index=True,
        nullable=False
    )
    
    # Uploader
    uploaded_by_user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        nullable=False
    )
    
    # Relationships
    task: Mapped["Task"] = relationship(back_populates="attachments")
    uploaded_by = relationship("User")
    
    __table_args__ = (
        CheckConstraint("file_size > 0", name="check_file_size_positive"),
    )


# =============================================================================
# TIME LOG MODEL
# =============================================================================

class TimeLog(Base):
    """
    Time logged on tasks.
    """
    __tablename__ = "time_logs"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    
    # Task reference
    task_id: Mapped[int] = mapped_column(
        ForeignKey("tasks.id", ondelete="CASCADE"),
        index=True,
        nullable=False
    )
    
    # User who logged time
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
        nullable=False
    )
    
    # Time logged (in minutes)
    minutes: Mapped[int] = mapped_column(Integer, nullable=False)
    
    # Work date
    work_date: Mapped[datetime.date] = mapped_column(Date, nullable=False)
    
    # Description
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Start/end time (optional for timer-based logging)
    started_at: Mapped[Optional[datetime.datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )
    ended_at: Mapped[Optional[datetime.datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )
    
    # Billable flag
    is_billable: Mapped[bool] = mapped_column(Boolean, default=True)
    
    # Relationships
    task: Mapped["Task"] = relationship(back_populates="time_logs")
    user = relationship("User")
    
    __table_args__ = (
        CheckConstraint("minutes > 0", name="check_time_log_minutes_positive"),
        Index("ix_time_logs_user_date", "user_id", "work_date"),
        Index("ix_time_logs_task_date", "task_id", "work_date"),
    )
