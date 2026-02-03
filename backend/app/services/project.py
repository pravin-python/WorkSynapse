from app.services.base import CRUDBase
from app.models.project.model import Project
from app.schemas.project import ProjectCreate, ProjectUpdate

class CRUDProject(CRUDBase[Project, ProjectCreate, ProjectUpdate]):
    pass

project = CRUDProject(Project)
