from sqlalchemy import String, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base

class Project(Base):
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String, index=True)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id"))

    owner = relationship("User", back_populates="projects")
    tasks = relationship("Task", back_populates="project")
