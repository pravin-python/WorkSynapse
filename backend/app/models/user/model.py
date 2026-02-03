from sqlalchemy import String, Boolean, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base
import enum

class UserRole(str, enum.Enum):
    ADMIN = "ADMIN"
    MANAGER = "MANAGER"
    DEVELOPER = "DEVELOPER"

class User(Base):
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    email: Mapped[str] = mapped_column(String, unique=True, index=True)
    full_name: Mapped[str] = mapped_column(String, index=True)
    hashed_password: Mapped[str] = mapped_column(String)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    role: Mapped[UserRole] = mapped_column(Enum(UserRole), default=UserRole.DEVELOPER)

    projects = relationship("Project", back_populates="owner")
    tasks = relationship("Task", back_populates="assignee")
    worklogs = relationship("WorkLog", back_populates="user")
    messages = relationship("Message", back_populates="sender")
