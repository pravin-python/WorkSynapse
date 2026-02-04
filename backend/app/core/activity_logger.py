from sqlalchemy import event, inspect
from sqlalchemy.orm import Session
from app.models.project.model import Project
from app.models.worklog.model import ActivityLog, ActivityType
from app.models.task.model import Task
import logging

logger = logging.getLogger(__name__)

def setup_activity_logging():
    """
    Setup SQLAlchemy event listeners for activity logging.
    Call this on app startup.
    """
    
    @event.listens_for(Project, 'after_insert')
    def log_project_create(mapper, connection, target):
        _log_event(connection, target, 'CREATE', 'projects', target.name)

    @event.listens_for(Project, 'after_update')
    def log_project_update(mapper, connection, target):
        _log_event(connection, target, 'UPDATE', 'projects', target.name)

    @event.listens_for(Task, 'after_insert')
    def log_task_create(mapper, connection, target):
        _log_event(connection, target, 'CREATE', 'tasks', target.title)

    logger.info("Activity logging event listeners registered.")

def _log_event(connection, target, action, resource_type, resource_name):
    """
    Internal helper to log event.
    Note: We try to infer user_id from the target object if available.
    """
    try:
        # Try to find user_id on the object
        user_id = None
        if hasattr(target, 'owner_id'):
            user_id = target.owner_id
        elif hasattr(target, 'created_by_user_id'):
            user_id = target.created_by_user_id
        elif hasattr(target, 'user_id'):
            user_id = target.user_id
            
        # Insert log directly via connection to avoid session issues in event handler
        connection.execute(
            ActivityLog.__table__.insert().values(
                user_id=user_id,
                activity_type=ActivityType.CREATE if action == 'CREATE' else ActivityType.UPDATE,
                resource_type=resource_type,
                resource_id=target.id,
                resource_name=resource_name,
                action=f"{resource_type}.{action.lower()}",
                description=f"{action} {resource_type}: {resource_name}",
                severity="INFO"
            )
        )
    except Exception as e:
        logger.error(f"Failed to log activity event: {e}")
