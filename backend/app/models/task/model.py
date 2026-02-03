from sqlalchemy import String, ForeignKey, Enum, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base
import enum

class TaskStatus(str, enum.Enum):
    TODO = "TODO"
    IN_PROGRESS = "IN_PROGRESS"
    REVIEW = "REVIEW"
    DONE = "DONE"

class TaskPriority(str, enum.Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"

class Task(Base):
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String, index=True)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    status: Mapped[TaskStatus] = mapped_column(Enum(TaskStatus), default=TaskStatus.TODO)
    priority: Mapped[TaskPriority] = mapped_column(Enum(TaskPriority), default=TaskPriority.MEDIUM)
    
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"))
    assignee_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=True)

    project = relationship("Project", back_populates="tasks")
    assignee = relationship("User", back_populates="tasks")
