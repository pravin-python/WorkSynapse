from sqlalchemy import String, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base

class Message(Base):
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    content: Mapped[str] = mapped_column(Text)
    sender_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    channel_id: Mapped[str] = mapped_column(String, index=True) # e.g., "project:1" or "dm:1:2"

    sender = relationship("User", back_populates="messages")
