from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Any, Dict, List

from app.api import deps
from app.models.user.model import User
from app.models.agent.model import Agent
from app.models.project.model import Project
from app.models.task.model import Task
from app.models.note.model import Note
from app.models.worklog.model import WorkLog, ActivityLog
from app.models.agent_chat.model import AgentConversation

router = APIRouter()

@router.get("/", response_model=Dict[str, List[Any]])
async def get_user_activity(
    db: AsyncSession = Depends(deps.get_db),
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
    result = await db.execute(select(Agent).filter(Agent.created_by_user_id == current_user.id))
    agents = result.scalars().all()
    
    # 2. Projects Created (Owned)
    result = await db.execute(select(Project).filter(Project.owner_id == current_user.id))
    projects = result.scalars().all()
    
    # 3. Tasks Created
    try:
        result = await db.execute(select(Task).filter(Task.created_by_id == current_user.id).limit(limit))
        tasks = result.scalars().all()
    except Exception:
        tasks = []

    # 4. Notes Created
    try:
        result = await db.execute(select(Note).filter(Note.owner_id == current_user.id).limit(limit))
        notes = result.scalars().all()
    except Exception:
        notes = []

    # 5. Agent Conversations
    try:
        result = await db.execute(select(AgentConversation).filter(AgentConversation.user_id == current_user.id).limit(limit))
        sessions = result.scalars().all()
    except Exception:
        sessions = []

    # 6. Work Logs
    try:
        result = await db.execute(select(WorkLog).filter(WorkLog.user_id == current_user.id).limit(limit))
        work_logs = result.scalars().all()
    except Exception:
        work_logs = []
        
    # 7. Activity Logs
    result = await db.execute(select(ActivityLog).filter(ActivityLog.user_id == current_user.id).order_by(ActivityLog.created_at.desc()).limit(limit))
    activity_logs = result.scalars().all()

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
async def get_user_activity_logs(
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
    skip: int = 0,
    limit: int = 50,
) -> Any:
    """
    Get specific activity logs for the user (audit trail).
    """
    result = await db.execute(
        select(ActivityLog)
        .filter(ActivityLog.user_id == current_user.id)
        .order_by(ActivityLog.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    logs = result.scalars().all()
    
    return [
        {k: v for k, v in log.__dict__.items() if not k.startswith('_')} 
        for log in logs
    ]
