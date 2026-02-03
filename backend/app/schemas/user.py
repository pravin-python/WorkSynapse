from typing import Optional
from pydantic import BaseModel, EmailStr
from app.models.user.model import UserRole

class UserBase(BaseModel):
    email: EmailStr
    full_name: str
    is_active: Optional[bool] = True
    role: UserRole = UserRole.DEVELOPER

class UserCreate(UserBase):
    password: str

class UserUpdate(UserBase):
    password: Optional[str] = None

class User(UserBase):
    id: int

    class Config:
        from_attributes = True
