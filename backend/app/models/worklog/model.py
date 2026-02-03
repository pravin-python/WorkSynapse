from sqlalchemy import String, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base

class WorkLog(Base):
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    duration_seconds: Mapped[int] = mapped_column(Integer, default=0)
    productivity_score: Mapped[int] = mapped_column(Integer, nullable=True) # 0-100
    active_window: Mapped[str] = mapped_column(String, nullable=True)

    user = relationship("User", back_populates="worklogs")
