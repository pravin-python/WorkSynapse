"""
WorkSynapse Manage Roles Command
================================
Command to manage roles and role-permission assignments.

Features:
- Create default system roles
- Assign default permissions to roles
- Add/remove permissions from roles dynamically
- Role hierarchy support
- Idempotent operations

Usage:
    # Initialize default roles
    python manage.py manage_roles
    
    # Add permission to role
    python manage.py add_permission --role Admin --permission agents.MANAGE
    
    # Remove permission from role
    python manage.py remove_permission --role Developer --permission projects.DELETE
"""

from typing import Dict, List, Optional, Set
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.commands.base_command import BaseCommand
from app.models.user.model import (
    Role, Permission, PermissionAction, UserRole, role_permissions
)


class ManageRolesCommand(BaseCommand):
    """
    Command to manage system roles and their permission assignments.
    
    This command handles:
    1. Creating default system roles
    2. Assigning default permissions based on role level
    3. Dynamic permission assignment/removal
    """
    
    name = "manage_roles"
    description = "Manage roles and default role-permission assignments"
    
    # Default role definitions with descriptions
    DEFAULT_ROLES: Dict[UserRole, str] = {
        UserRole.SUPER_ADMIN: "Full system access with no restrictions",
        UserRole.ADMIN: "Administrative access for project and user management",
        UserRole.MANAGER: "Project, task, and team management capabilities",
        UserRole.TEAM_LEAD: "Team leadership with task assignment abilities",
        UserRole.DEVELOPER: "Development access for tasks and chat",
        UserRole.VIEWER: "Read-only access to projects and tasks",
        UserRole.GUEST: "Limited guest access",
    }
    
    # Role -> Permission mapping (resource patterns that each role gets)
    # SuperAdmin gets everything, so not listed here
    ROLE_PERMISSION_MAP: Dict[str, Dict[str, Set[str]]] = {
        "ADMIN": {
            # Resource: set of allowed actions
            "projects": {"CREATE", "READ", "UPDATE", "DELETE", "MANAGE", "EXPORT"},
            "tasks": {"CREATE", "READ", "UPDATE", "DELETE", "MANAGE", "APPROVE"},
            "users": {"CREATE", "READ", "UPDATE", "DELETE", "MANAGE"},
            "agents": {"CREATE", "READ", "UPDATE", "DELETE", "EXECUTE", "MANAGE"},
            "reports": {"CREATE", "READ", "EXPORT", "MANAGE"},
            "teams": {"CREATE", "READ", "UPDATE", "DELETE", "MANAGE"},
            "messages": {"CREATE", "READ", "DELETE", "MANAGE"},
            "roles": {"READ", "UPDATE"},
            "settings": {"READ", "UPDATE"},
            "worklogs": {"READ", "UPDATE", "APPROVE"},
            "api_keys": {"CREATE", "READ", "DELETE", "MANAGE"},
            "audit_logs": {"READ", "EXPORT"},
        },
        "MANAGER": {
            "projects": {"CREATE", "READ", "UPDATE", "EXPORT"},
            "tasks": {"CREATE", "READ", "UPDATE", "DELETE", "MANAGE", "APPROVE"},
            "users": {"READ"},
            "agents": {"READ", "EXECUTE"},
            "reports": {"CREATE", "READ", "EXPORT"},
            "teams": {"CREATE", "READ", "UPDATE", "MANAGE"},
            "messages": {"CREATE", "READ", "DELETE"},
            "worklogs": {"CREATE", "READ", "UPDATE", "APPROVE"},
        },
        "TEAM_LEAD": {
            "projects": {"READ"},
            "tasks": {"CREATE", "READ", "UPDATE", "APPROVE"},
            "users": {"READ"},
            "agents": {"READ", "EXECUTE"},
            "reports": {"READ"},
            "teams": {"READ", "UPDATE"},
            "messages": {"CREATE", "READ"},
            "worklogs": {"CREATE", "READ", "UPDATE", "APPROVE"},
        },
        "DEVELOPER": {
            "projects": {"READ"},
            "tasks": {"CREATE", "READ", "UPDATE"},
            "agents": {"READ", "EXECUTE"},
            "reports": {"READ"},
            "teams": {"READ"},
            "messages": {"CREATE", "READ"},
            "worklogs": {"CREATE", "READ", "UPDATE"},
        },
        "VIEWER": {
            "projects": {"READ"},
            "tasks": {"READ"},
            "reports": {"READ"},
            "teams": {"READ"},
            "messages": {"READ"},
        },
        "GUEST": {
            "projects": {"READ"},
            "tasks": {"READ"},
        },
    }
    
    async def execute(
        self,
        db: AsyncSession,
        role_name: Optional[str] = None,
        add_permission: Optional[str] = None,
        remove_permission: Optional[str] = None,
        **kwargs
    ) -> dict:
        """
        Execute role management operations.
        
        If role_name is None, creates/updates all default roles.
        If add_permission or remove_permission is specified, modifies that role.
        
        Args:
            db: Database session
            role_name: Optional specific role to manage
            add_permission: Permission to add (format: resource.ACTION)
            remove_permission: Permission to remove (format: resource.ACTION)
        
        Returns:
            dict with operation results
        """
        self.output.header("Managing System Roles")
        
        results = {
            "roles_created": 0,
            "roles_updated": 0,
            "permissions_assigned": 0,
        }
        
        if add_permission and role_name:
            return await self._add_permission_to_role(db, role_name, add_permission)
        
        if remove_permission and role_name:
            return await self._remove_permission_from_role(db, role_name, remove_permission)
        
        # Default: ensure all roles exist with proper permissions
        results = await self._ensure_default_roles(db)
        
        return results
    
    async def _ensure_default_roles(self, db: AsyncSession) -> dict:
        """
        Ensure all default roles exist and have proper permissions.
        """
        results = {"roles_created": 0, "roles_updated": 0, "permissions_assigned": 0}
        
        # Step 1: Create roles if they don't exist
        self.output.info("Checking system roles...")
        
        for role_enum, description in self.DEFAULT_ROLES.items():
            role_name = role_enum.value
            
            stmt = select(Role).where(Role.name == role_name)
            result = await db.execute(stmt)
            role = result.scalars().first()
            
            if not role:
                role = Role(
                    name=role_name,
                    description=description,
                    is_system=True,
                    is_active=True
                )
                db.add(role)
                results["roles_created"] += 1
                self.output.bullet(f"Created role: {role_name}")
            else:
                self.logger.debug(f"Role exists: {role_name}")
        
        await db.flush()
        
        # Step 2: Assign default permissions
        self.output.info("Assigning default permissions...")
        results["permissions_assigned"] = await self._assign_default_permissions(db)
        
        # Summary
        self.output.divider()
        self.output.table_row("Roles Created", str(results["roles_created"]))
        self.output.table_row("Permissions Assigned", str(results["permissions_assigned"]))
        self.output.divider()
        
        if results["roles_created"] > 0 or results["permissions_assigned"] > 0:
            self.output.success("Role management completed successfully")
        else:
            self.output.info("All roles already configured correctly")
        
        return results
    
    async def _assign_default_permissions(self, db: AsyncSession) -> int:
        """
        Assign default permissions to each role based on ROLE_PERMISSION_MAP.
        Returns count of total assignments made.
        """
        assignment_count = 0
        
        # Fetch all permissions
        stmt = select(Permission).where(Permission.is_active == True)
        result = await db.execute(stmt)
        all_permissions = {
            (p.resource, p.action.value): p 
            for p in result.scalars().all()
        }
        
        if not all_permissions:
            self.output.warning("No permissions found. Run 'seed_permissions' first.")
            return 0
        
        # Helper to get role
        async def get_role(name: str) -> Optional[Role]:
            r = await db.execute(select(Role).where(Role.name == name))
            return r.scalars().first()
        
        # Assign permissions to each role
        for role_name, resource_actions in self.ROLE_PERMISSION_MAP.items():
            role = await get_role(role_name)
            if not role:
                self.logger.warning(f"Role not found: {role_name}")
                continue
            
            # Get current permissions for this role
            current_perms = set((p.resource, p.action.value) for p in role.permissions)
            
            for resource, actions in resource_actions.items():
                for action in actions:
                    perm_key = (resource, action)
                    
                    # Skip if already assigned
                    if perm_key in current_perms:
                        continue
                    
                    # Find permission
                    permission = all_permissions.get(perm_key)
                    if permission and permission not in role.permissions:
                        role.permissions.append(permission)
                        assignment_count += 1
                        self.logger.debug(f"Assigned {resource}.{action} to {role_name}")
        
        await db.flush()
        return assignment_count
    
    async def _add_permission_to_role(
        self,
        db: AsyncSession,
        role_name: str,
        permission_str: str
    ) -> dict:
        """
        Add a specific permission to a role.
        
        Args:
            role_name: Name of the role (e.g., "Admin")
            permission_str: Permission string (e.g., "agents.MANAGE")
        """
        self.output.info(f"Adding permission '{permission_str}' to role '{role_name}'")
        
        # Parse permission string
        try:
            resource, action_str = permission_str.split(".")
            action = PermissionAction(action_str)
        except (ValueError, KeyError):
            self.output.error(f"Invalid permission format: {permission_str}")
            self.output.info("Expected format: resource.ACTION (e.g., agents.MANAGE)")
            return {"success": False, "error": "Invalid permission format"}
        
        # Find role
        stmt = select(Role).where(Role.name == role_name)
        result = await db.execute(stmt)
        role = result.scalars().first()
        
        if not role:
            self.output.error(f"Role not found: {role_name}")
            return {"success": False, "error": "Role not found"}
        
        # Find permission
        stmt = select(Permission).where(
            Permission.resource == resource,
            Permission.action == action
        )
        result = await db.execute(stmt)
        permission = result.scalars().first()
        
        if not permission:
            self.output.error(f"Permission not found: {permission_str}")
            return {"success": False, "error": "Permission not found"}
        
        # Check if already assigned
        if permission in role.permissions:
            self.output.warning(f"Permission already assigned to role")
            return {"success": True, "message": "Already assigned"}
        
        # Assign permission
        role.permissions.append(permission)
        await db.flush()
        
        self.output.success(f"Added '{permission_str}' to role '{role_name}'")
        return {"success": True, "message": "Permission added"}
    
    async def _remove_permission_from_role(
        self,
        db: AsyncSession,
        role_name: str,
        permission_str: str
    ) -> dict:
        """
        Remove a specific permission from a role.
        
        Args:
            role_name: Name of the role (e.g., "Admin")
            permission_str: Permission string (e.g., "projects.DELETE")
        """
        self.output.info(f"Removing permission '{permission_str}' from role '{role_name}'")
        
        # Parse permission string
        try:
            resource, action_str = permission_str.split(".")
            action = PermissionAction(action_str)
        except (ValueError, KeyError):
            self.output.error(f"Invalid permission format: {permission_str}")
            self.output.info("Expected format: resource.ACTION (e.g., projects.DELETE)")
            return {"success": False, "error": "Invalid permission format"}
        
        # Find role
        stmt = select(Role).where(Role.name == role_name)
        result = await db.execute(stmt)
        role = result.scalars().first()
        
        if not role:
            self.output.error(f"Role not found: {role_name}")
            return {"success": False, "error": "Role not found"}
        
        # Find permission
        stmt = select(Permission).where(
            Permission.resource == resource,
            Permission.action == action
        )
        result = await db.execute(stmt)
        permission = result.scalars().first()
        
        if not permission:
            self.output.error(f"Permission not found: {permission_str}")
            return {"success": False, "error": "Permission not found"}
        
        # Check if assigned
        if permission not in role.permissions:
            self.output.warning(f"Permission not assigned to role")
            return {"success": True, "message": "Not assigned"}
        
        # Remove permission
        role.permissions.remove(permission)
        await db.flush()
        
        self.output.success(f"Removed '{permission_str}' from role '{role_name}'")
        return {"success": True, "message": "Permission removed"}


class AddPermissionCommand(BaseCommand):
    """
    Dedicated command to add a permission to a role.
    
    Usage:
        python manage.py add_permission --role Admin --permission agents.MANAGE
    """
    
    name = "add_permission"
    description = "Add a permission to a role"
    
    async def execute(
        self,
        db: AsyncSession,
        role: str,
        permission: str,
        **kwargs
    ) -> dict:
        """Add permission to role."""
        mgr = ManageRolesCommand()
        return await mgr._add_permission_to_role(db, role, permission)


class RemovePermissionCommand(BaseCommand):
    """
    Dedicated command to remove a permission from a role.
    
    Usage:
        python manage.py remove_permission --role Developer --permission projects.DELETE
    """
    
    name = "remove_permission"
    description = "Remove a permission from a role"
    
    async def execute(
        self,
        db: AsyncSession,
        role: str,
        permission: str,
        **kwargs
    ) -> dict:
        """Remove permission from role."""
        mgr = ManageRolesCommand()
        return await mgr._remove_permission_from_role(db, role, permission)
