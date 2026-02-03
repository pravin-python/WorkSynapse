from typing import Optional
from pydantic import BaseModel

class ProjectBase(BaseModel):
    name: str
    description: Optional[str] = None

class ProjectCreate(ProjectBase):
    pass

class ProjectUpdate(ProjectBase):
    pass

class Project(ProjectBase):
    id: int
    owner_id: int

    class Config:
        from_attributes = True
