"""
WorkSynapse Work Tracking Models
================================
Comprehensive work tracking with activity logging and usage analytics.

Features:
- Work session logging
- Activity/event logging
- Application usage tracking
- Idle period detection
- Productivity metrics
"""
from typing import List, Optional
from sqlalchemy import (
    String, Boolean, Enum, ForeignKey, Text, Integer, 
    DateTime, Index, UniqueConstraint, CheckConstraint,
    JSON, Float, Date
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base
import enum
import datetime


# =============================================================================
# ENUMS
# =============================================================================

class WorkLogType(str, enum.Enum):
    """Work log types."""
    MANUAL = "MANUAL"           # User-entered time
    TIMER = "TIMER"             # Timer-tracked
    AUTO_DETECTED = "AUTO_DETECTED"  # Auto-detected from activity
    IMPORTED = "IMPORTED"       # Imported from external system


class ActivityType(str, enum.Enum):
    """Activity/event types."""
    # User actions
    LOGIN = "LOGIN"
    LOGOUT = "LOGOUT"
    PAGE_VIEW = "PAGE_VIEW"
    BUTTON_CLICK = "BUTTON_CLICK"
    FORM_SUBMIT = "FORM_SUBMIT"
    
    # CRUD operations
    CREATE = "CREATE"
    READ = "READ"
    UPDATE = "UPDATE"
    DELETE = "DELETE"
    
    # Collaboration
    COMMENT_ADD = "COMMENT_ADD"
    FILE_UPLOAD = "FILE_UPLOAD"
    FILE_DOWNLOAD = "FILE_DOWNLOAD"
    SHARE = "SHARE"
    MENTION = "MENTION"
    
    # Status changes
    STATUS_CHANGE = "STATUS_CHANGE"
    ASSIGNMENT_CHANGE = "ASSIGNMENT_CHANGE"
    
    # System events
    SYSTEM_ERROR = "SYSTEM_ERROR"
    SYSTEM_WARNING = "SYSTEM_WARNING"
    INTEGRATION_SYNC = "INTEGRATION_SYNC"
    
    # Security events
    PERMISSION_CHANGE = "PERMISSION_CHANGE"
    PASSWORD_CHANGE = "PASSWORD_CHANGE"
    MFA_ENABLE = "MFA_ENABLE"
    MFA_DISABLE = "MFA_DISABLE"
    SUSPICIOUS_ACTIVITY = "SUSPICIOUS_ACTIVITY"


class IdlePeriodType(str, enum.Enum):
    """Idle period types."""
    BREAK = "BREAK"
    LUNCH = "LUNCH"
    MEETING = "MEETING"
    AWAY = "AWAY"
    DISCONNECT = "DISCONNECT"
    UNKNOWN = "UNKNOWN"


# =============================================================================
# WORK LOG MODEL
# =============================================================================

class WorkLog(Base):
    """
    Work session logging.
    
    Tracks time spent working, productivity scores, and application usage.
    """
    __tablename__ = "work_logs"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    
    # User reference
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
        nullable=False
    )
    
    # Task reference (optional)
    task_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("tasks.id", ondelete="SET NULL"),
        index=True,
        nullable=True
    )
    
    # Project reference (optional, derived from task or explicit)
    project_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("projects.id", ondelete="SET NULL"),
        index=True,
        nullable=True
    )
    
    # Log type
    log_type: Mapped[WorkLogType] = mapped_column(
        Enum(WorkLogType),
        default=WorkLogType.MANUAL
    )
    
    # Time tracking
    work_date: Mapped[datetime.date] = mapped_column(Date, nullable=False)
    started_at: Mapped[Optional[datetime.datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )
    ended_at: Mapped[Optional[datetime.datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )
    duration_seconds: Mapped[int] = mapped_column(Integer, default=0)
    
    # Description
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Productivity metrics
    productivity_score: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # 0-100
    focus_score: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # 0-100
    
    # Active window tracking (from desktop app)
    active_window: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    active_application: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    
    # Keystroke/mouse activity (for productivity detection)
    keystroke_count: Mapped[int] = mapped_column(Integer, default=0)
    mouse_click_count: Mapped[int] = mapped_column(Integer, default=0)
    mouse_distance_pixels: Mapped[int] = mapped_column(Integer, default=0)
    
    # Screenshot tracking (optional)
    screenshot_count: Mapped[int] = mapped_column(Integer, default=0)
    
    # Billable flag
    is_billable: Mapped[bool] = mapped_column(Boolean, default=True)
    
    # Synced from external system
    external_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    external_source: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="worklogs")
    task = relationship("Task")
    project = relationship("Project")
    
    __table_args__ = (
        CheckConstraint("duration_seconds >= 0", name="check_duration_positive"),
        CheckConstraint(
            "productivity_score IS NULL OR (productivity_score >= 0 AND productivity_score <= 100)",
            name="check_productivity_range"
        ),
        CheckConstraint(
            "focus_score IS NULL OR (focus_score >= 0 AND focus_score <= 100)",
            name="check_focus_range"
        ),
        Index("ix_work_logs_user_date", "user_id", "work_date"),
        Index("ix_work_logs_task", "task_id"),
        Index("ix_work_logs_project", "project_id"),
    )


# =============================================================================
# ACTIVITY LOG MODEL
# =============================================================================

class ActivityLog(Base):
    """
    Comprehensive activity/event logging for audit trail.
    
    Logs all significant actions in the system for:
    - Security auditing
    - User behavior analytics
    - Debugging
    - Compliance
    """
    __tablename__ = "activity_logs"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    
    # Who performed the action
    user_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        index=True,
        nullable=True  # Nullable for system events
    )
    
    # Activity type
    activity_type: Mapped[ActivityType] = mapped_column(
        Enum(ActivityType),
        nullable=False,
        index=True
    )
    
    # What was affected
    resource_type: Mapped[str] = mapped_column(String(50), nullable=False)  # task, project, user, etc.
    resource_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    resource_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)  # Human-readable name
    
    # Action details
    action: Mapped[str] = mapped_column(String(100), nullable=False)  # e.g., "task.status.update"
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Change details (for updates)
    old_values: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    new_values: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    
    # Request context
    ip_address: Mapped[Optional[str]] = mapped_column(String(45), nullable=True)
    user_agent: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    request_method: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    request_path: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    
    # Session reference
    session_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    
    # Severity level
    severity: Mapped[str] = mapped_column(String(20), default="INFO")  # DEBUG, INFO, WARNING, ERROR, CRITICAL
    
    # Additional metadata
    extra_metadata: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    
    # Performance tracking
    duration_ms: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    
    # Relationships
    user = relationship("User")
    
    __table_args__ = (
        Index("ix_activity_logs_user_created", "user_id", "created_at"),
        Index("ix_activity_logs_type_created", "activity_type", "created_at"),
        Index("ix_activity_logs_resource", "resource_type", "resource_id"),
        Index("ix_activity_logs_severity", "severity", "created_at"),
        Index("ix_activity_logs_ip", "ip_address"),
    )


# =============================================================================
# APP USAGE MODEL
# =============================================================================

class AppUsage(Base):
    """
    Application usage tracking from desktop app.
    
    Tracks which applications are being used during work hours.
    """
    __tablename__ = "app_usages"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    
    # User reference
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
        nullable=False
    )
    
    # Date for aggregation
    usage_date: Mapped[datetime.date] = mapped_column(Date, nullable=False)
    
    # Application info
    application_name: Mapped[str] = mapped_column(String(255), nullable=False)
    application_path: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    window_title: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    
    # Category (for productivity scoring)
    category: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)  # productive, neutral, distracting
    is_productive: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    
    # Usage metrics
    duration_seconds: Mapped[int] = mapped_column(Integer, default=0)
    focus_time_seconds: Mapped[int] = mapped_column(Integer, default=0)  # Active usage time
    
    # Activity metrics
    keystroke_count: Mapped[int] = mapped_column(Integer, default=0)
    mouse_click_count: Mapped[int] = mapped_column(Integer, default=0)
    
    # Session count (how many times opened)
    session_count: Mapped[int] = mapped_column(Integer, default=1)
    
    # Relationships
    user = relationship("User")
    
    __table_args__ = (
        UniqueConstraint("user_id", "usage_date", "application_name", name="uq_app_usage_daily"),
        CheckConstraint("duration_seconds >= 0", name="check_app_duration_positive"),
        Index("ix_app_usages_user_date", "user_id", "usage_date"),
        Index("ix_app_usages_category", "category"),
    )


# =============================================================================
# IDLE PERIOD MODEL
# =============================================================================

class IdlePeriod(Base):
    """
    Idle period tracking from desktop app.
    
    Detects and logs periods of inactivity.
    """
    __tablename__ = "idle_periods"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    
    # User reference
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
        nullable=False
    )
    
    # Idle period timing
    started_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False
    )
    ended_at: Mapped[Optional[datetime.datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )
    duration_seconds: Mapped[int] = mapped_column(Integer, default=0)
    
    # Idle type
    idle_type: Mapped[IdlePeriodType] = mapped_column(
        Enum(IdlePeriodType),
        default=IdlePeriodType.UNKNOWN
    )
    
    # User-provided reason (optional)
    reason: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    
    # Detection method
    detection_method: Mapped[str] = mapped_column(
        String(50),
        default="auto"  # auto, manual, scheduled
    )
    
    # Last active window before idle
    last_active_window: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    last_active_application: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    
    # Relationships
    user = relationship("User")
    
    __table_args__ = (
        CheckConstraint("duration_seconds >= 0", name="check_idle_duration_positive"),
        Index("ix_idle_periods_user_started", "user_id", "started_at"),
        Index("ix_idle_periods_type", "idle_type"),
    )


# =============================================================================
# PRODUCTIVITY SUMMARY MODEL
# =============================================================================

class ProductivitySummary(Base):
    """
    Daily productivity summary per user.
    
    Aggregated metrics for productivity dashboards.
    """
    __tablename__ = "productivity_summaries"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    
    # User reference
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
        nullable=False
    )
    
    # Summary date
    summary_date: Mapped[datetime.date] = mapped_column(Date, nullable=False)
    
    # Time metrics (in seconds)
    total_active_time: Mapped[int] = mapped_column(Integer, default=0)
    total_productive_time: Mapped[int] = mapped_column(Integer, default=0)
    total_neutral_time: Mapped[int] = mapped_column(Integer, default=0)
    total_distracting_time: Mapped[int] = mapped_column(Integer, default=0)
    total_idle_time: Mapped[int] = mapped_column(Integer, default=0)
    
    # Scores (0-100)
    productivity_score: Mapped[int] = mapped_column(Integer, default=0)
    focus_score: Mapped[int] = mapped_column(Integer, default=0)
    
    # Activity metrics
    total_keystrokes: Mapped[int] = mapped_column(Integer, default=0)
    total_mouse_clicks: Mapped[int] = mapped_column(Integer, default=0)
    
    # Task metrics
    tasks_completed: Mapped[int] = mapped_column(Integer, default=0)
    tasks_created: Mapped[int] = mapped_column(Integer, default=0)
    
    # Top applications (JSON array)
    top_applications: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    
    # Trends
    score_trend: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)  # up, down, stable
    
    # Relationships
    user = relationship("User")
    
    __table_args__ = (
        UniqueConstraint("user_id", "summary_date", name="uq_productivity_summary_daily"),
        CheckConstraint(
            "productivity_score >= 0 AND productivity_score <= 100",
            name="check_prod_score_range"
        ),
        CheckConstraint(
            "focus_score >= 0 AND focus_score <= 100",
            name="check_focus_score_range"
        ),
        Index("ix_productivity_summaries_user_date", "user_id", "summary_date"),
    )


# =============================================================================
# SECURITY AUDIT LOG MODEL
# =============================================================================

class SecurityAuditLog(Base):
    """
    Security-specific audit logging.
    
    Critical security events that require special attention and retention.
    """
    __tablename__ = "security_audit_logs"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    
    # Event classification
    event_type: Mapped[str] = mapped_column(String(100), nullable=False)  # login_failed, permission_denied, etc.
    severity: Mapped[str] = mapped_column(String(20), nullable=False)  # LOW, MEDIUM, HIGH, CRITICAL
    
    # Who/what triggered
    user_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        index=True,
        nullable=True
    )
    email_attempted: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    
    # Request context
    ip_address: Mapped[str] = mapped_column(String(45), nullable=False)
    user_agent: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    
    # Resource affected
    resource_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    resource_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    
    # Event details
    description: Mapped[str] = mapped_column(Text, nullable=False)
    details: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    
    # Geographic info (from IP lookup)
    country: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    city: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    
    # Risk scoring
    risk_score: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # 0-100
    
    # Response taken
    action_taken: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    
    # Investigation status
    is_investigated: Mapped[bool] = mapped_column(Boolean, default=False)
    investigated_by_user_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("users.id"),
        nullable=True
    )
    investigation_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Relationships
    user = relationship("User", foreign_keys=[user_id])
    investigated_by = relationship("User", foreign_keys=[investigated_by_user_id])
    
    __table_args__ = (
        Index("ix_security_audit_type_created", "event_type", "created_at"),
        Index("ix_security_audit_severity", "severity", "created_at"),
        Index("ix_security_audit_ip", "ip_address"),
        Index("ix_security_audit_user", "user_id", "created_at"),
    )
