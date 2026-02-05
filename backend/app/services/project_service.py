"""
WorkSynapse Project Service
===========================
Service layer for project operations including:
- Project CRUD operations
- Project member management
- Project status management
"""

from typing import Any, Dict, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import logging

from app.services.base import SecureCRUDBase, NotFoundError
from app.models.project.model import Project, ProjectStatus
from app.schemas.project import ProjectCreate, ProjectUpdate

logger = logging.getLogger(__name__)


class ProjectService(SecureCRUDBase[Project, ProjectCreate, ProjectUpdate]):
    """
    Project service for project-related operations.
    
    Provides:
    - Standard CRUD operations
    - Project member management
    - Status transitions
    """
    
    def __init__(self):
        super().__init__(Project)
    
    async def get_user_projects(
        self,
        db: AsyncSession,
        user_id: int,
        include_archived: bool = False,
    ) -> List[Project]:
        """
        Get all projects for a user.
        
        Args:
            db: Database session
            user_id: User ID
            include_archived: Whether to include archived projects
            
        Returns:
            List of projects
        """
        stmt = select(Project).where(
            Project.members.any(id=user_id)
        )
        
        if not include_archived:
            stmt = stmt.where(Project.status != ProjectStatus.ARCHIVED)
        
        stmt = stmt.order_by(Project.updated_at.desc())
        
        result = await db.execute(stmt)
        return list(result.scalars().all())
    
    async def get_by_status(
        self,
        db: AsyncSession,
        status: ProjectStatus,
    ) -> List[Project]:
        """
        Get projects by status.
        
        Args:
            db: Database session
            status: Project status to filter by
            
        Returns:
            List of projects
        """
        stmt = select(Project).where(Project.status == status)
        result = await db.execute(stmt)
        return list(result.scalars().all())
    
    async def update_status(
        self,
        db: AsyncSession,
        project_id: int,
        new_status: ProjectStatus,
    ) -> Project:
        """
        Update project status.
        
        Args:
            db: Database session
            project_id: Project ID
            new_status: New status
            
        Returns:
            Updated project
            
        Raises:
            NotFoundError: If project not found
        """
        project = await self.get(db, project_id)
        if not project:
            raise NotFoundError(f"Project {project_id} not found")
        
        project.status = new_status
        await db.commit()
        await db.refresh(project)
        
        logger.info(f"Project {project_id} status updated to {new_status}")
        return project
    
    async def add_member(
        self,
        db: AsyncSession,
        project_id: int,
        user_id: int,
    ) -> Project:
        """
        Add a member to a project.
        
        Args:
            db: Database session
            project_id: Project ID
            user_id: User ID to add
            
        Returns:
            Updated project
        """
        from app.models.user.model import User
        
        project = await self.get(db, project_id)
        if not project:
            raise NotFoundError(f"Project {project_id} not found")
        
        stmt = select(User).where(User.id == user_id)
        result = await db.execute(stmt)
        user = result.scalars().first()
        
        if not user:
            raise NotFoundError(f"User {user_id} not found")
        
        if user not in project.members:
            project.members.append(user)
            await db.commit()
            logger.info(f"Added user {user_id} to project {project_id}")
        
        await db.refresh(project)
        return project
    
    async def remove_member(
        self,
        db: AsyncSession,
        project_id: int,
        user_id: int,
    ) -> Project:
        """
        Remove a member from a project.
        
        Args:
            db: Database session
            project_id: Project ID
            user_id: User ID to remove
            
        Returns:
            Updated project
        """
        from app.models.user.model import User
        
        project = await self.get(db, project_id)
        if not project:
            raise NotFoundError(f"Project {project_id} not found")
        
        stmt = select(User).where(User.id == user_id)
        result = await db.execute(stmt)
        user = result.scalars().first()
        
        if user and user in project.members:
            project.members.remove(user)
            await db.commit()
            logger.info(f"Removed user {user_id} from project {project_id}")
        
        await db.refresh(project)
        return project


# Singleton instance
project_service = ProjectService()
