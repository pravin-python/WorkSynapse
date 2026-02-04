from sqlalchemy.orm import Session
from app.models.worklog.model import ActivityLog
from typing import Optional, Any, Dict

def log_user_activity(
    db: Session,
    user_id: int,
    action: str,
    entity_type: str,
    entity_id: int,
    description: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> ActivityLog:
    """
    Log a user activity to the database.
    """
    activity = ActivityLog(
        user_id=user_id,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        description=description,
        metadata_json=metadata or {}
    )
    db.add(activity)
    db.commit()
    db.refresh(activity)
    return activity
