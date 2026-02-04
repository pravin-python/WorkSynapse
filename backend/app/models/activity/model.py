"""
WorkSynapse Activity Log Model
==============================
Tracks detailed user activity for audit trails and monitoring.
"""
from typing import Optional, Dict, Any
from sqlalchemy import String, Integer, DateTime, ForeignKey, Text, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
import datetime

from app.models.base import Base

class ActivityLog(Base):
    """
    Activity Log model to store audit trail of user actions.
    """
    __tablename__ = "activity_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    
    # Who performed the action
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    
    # What did they do
    action: Mapped[str] = mapped_column(String(100), nullable=False)  # e.g., 'created', 'updated', 'deleted'
    
    # What entity was affected
    entity_type: Mapped[str] = mapped_column(String(50), nullable=False)  # e.g., 'Agent', 'Project'
    entity_id: Mapped[int] = mapped_column(Integer, nullable=False)
    
    # Description/Details
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    metadata_json: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)
    
    # When
    timestamp: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), 
        server_default="now()",
        index=True
    )

    # Relationships
    user = relationship("User", backref="activity_logs")

    def __repr__(self) -> str:
        return f"<ActivityLog(user={self.user_id}, action='{self.action}', entity='{self.entity_type}')>"
