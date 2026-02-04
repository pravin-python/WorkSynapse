from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Any, Dict, List

from app.api import deps
from app.models.user.model import User
from app.models.agent.model import Agent
from app.models.project.model import Project
from app.models.task.model import Task
from app.models.note.model import Note
from app.models.worklog.model import WorkLog, ActivityLog

router = APIRouter()

@router.get("/", response_model=Dict[str, List[Any]])
def get_user_activity(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
    skip: int = 0,
    limit: int = 100,
) -> Any:
    """
    Get all activity and entities created by the current user.
    """
    
    # helper to format response
    def format_list(items):
        return [
            {k: v for k, v in item.__dict__.items() if not k.startswith('_')} 
            for item in items
        ]

    # 1. Agents Created
    agents = db.query(Agent).filter(Agent.user_id == current_user.id).all()
    
    # 2. Projects Created (Owned)
    projects = db.query(Project).filter(Project.owner_id == current_user.id).all()
    
    # 3. Tasks Created
    # Note: Using created_by_user_id based on User model relationship
    try:
        tasks = db.query(Task).filter(Task.created_by_user_id == current_user.id).limit(limit).all()
    except Exception:
        # Fallback if field name differs (e.g. might be user_id or creator_id)
        # Using a safer generic try/except to avoid crashing the whole endpoint
        tasks = []

    # 4. Notes Created
    try:
        notes = db.query(Note).filter(Note.owner_id == current_user.id).limit(limit).all()
    except Exception:
        notes = []

    # 5. Agent Sessions
    try:
        sessions = db.query(AgentSession).filter(AgentSession.user_id == current_user.id).limit(limit).all()
    except Exception:
        sessions = []

    # 6. Work Logs
    try:
        work_logs = db.query(WorkLog).filter(WorkLog.user_id == current_user.id).limit(limit).all()
    except Exception:
        work_logs = []
        
    # 7. Activity Logs
    activity_logs = db.query(ActivityLog).filter(ActivityLog.user_id == current_user.id).order_by(ActivityLog.timestamp.desc()).limit(limit).all()

    return {
        "agents": format_list(agents),
        "projects": format_list(projects),
        "tasks": format_list(tasks),
        "notes": format_list(notes),
        "sessions": format_list(sessions),
        "work_logs": format_list(work_logs),
        "activity_logs": format_list(activity_logs)
    }

@router.get("/logs", response_model=List[Any])
def get_user_activity_logs(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
    skip: int = 0,
    limit: int = 50,
) -> Any:
    """
    Get specific activity logs for the user (audit trail).
    """
    logs = db.query(ActivityLog).filter(ActivityLog.user_id == current_user.id)\
        .order_by(ActivityLog.timestamp.desc())\
        .offset(skip)\
        .limit(limit)\
        .all()
    
    return [
        {k: v for k, v in log.__dict__.items() if not k.startswith('_')} 
        for log in logs
    ]
