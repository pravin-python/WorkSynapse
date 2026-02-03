from typing import Optional
from pydantic import BaseModel
from app.models.task.model import TaskStatus, TaskPriority

class TaskBase(BaseModel):
    title: str
    description: Optional[str] = None
    status: TaskStatus = TaskStatus.TODO
    priority: TaskPriority = TaskPriority.MEDIUM
    project_id: int
    assignee_id: Optional[int] = None

class TaskCreate(TaskBase):
    pass

class TaskUpdate(TaskBase):
    pass

class Task(TaskBase):
    id: int

    class Config:
        from_attributes = True
