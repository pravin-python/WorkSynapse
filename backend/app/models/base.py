from typing import Any
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import DateTime, func
import datetime

class Base(DeclarativeBase):
    id: Any
    __name__: str
    
    # Generate __tablename__ automatically
    @declared_attr
    def __tablename__(cls) -> str:
        return cls.__name__.lower() + 's'

    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), 
        server_default=func.now(), 
        onupdate=func.now()
    )
