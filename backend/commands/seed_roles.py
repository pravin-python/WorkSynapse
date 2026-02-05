"""
WorkSynapse Seed Roles Command
==============================
Dedicated command to create default system roles with proper permissions.

This is a convenience wrapper around ManageRolesCommand for initializing
the RBAC system with default roles.

Usage:
    python manage.py seed_roles

Roles Created:
- SuperAdmin: Full system access with no restrictions
- Admin: Administrative access for project and user management
- Manager: Project, task, and team management capabilities
- TeamLead: Team leadership with task assignment abilities
- Developer: Development access for tasks and chat
- Viewer: Read-only access to projects and tasks
- Guest: Limited guest access

Note: Run seed_permissions first to ensure all permissions exist.
"""

from typing import Dict, List, Optional, Set
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from commands.base_command import BaseCommand
from app.models.user.model import (
    Role, Permission, PermissionAction, UserRole, role_permissions
)


class SeedRolesCommand(BaseCommand):
    """
    Command to seed default system roles with their permission assignments.
    
    This command:
    1. Creates all default system roles if they don't exist
    2. Assigns appropriate permissions to each role based on role level
    3. Is idempotent - safe to run multiple times
    """
    
    name = "seed_roles"
    description = "Seed default system roles with proper permissions"
    
    # Default role definitions with descriptions and levels
    DEFAULT_ROLES: Dict[str, dict] = {
        "SuperAdmin": {
            "description": "Full system access with no restrictions",
            "level": 0,  # Highest privilege
            "is_system": True,
        },
        "Admin": {
            "description": "Administrative access for project and user management",
            "level": 1,
            "is_system": True,
        },
        "Manager": {
            "description": "Project, task, and team management capabilities",
            "level": 2,
            "is_system": True,
        },
        "TeamLead": {
            "description": "Team leadership with task assignment abilities",
            "level": 3,
            "is_system": True,
        },
        "Developer": {
            "description": "Development access for tasks and chat",
            "level": 4,
            "is_system": True,
        },
        "Viewer": {
            "description": "Read-only access to projects and tasks",
            "level": 5,
            "is_system": True,
        },
        "Guest": {
            "description": "Limited guest access",
            "level": 6,
            "is_system": True,
        },
    }
    
    # Role -> Permission mapping
    ROLE_PERMISSIONS: Dict[str, Dict[str, Set[str]]] = {
        "Admin": {
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
        "Manager": {
            "projects": {"CREATE", "READ", "UPDATE", "EXPORT"},
            "tasks": {"CREATE", "READ", "UPDATE", "DELETE", "MANAGE", "APPROVE"},
            "users": {"READ"},
            "agents": {"READ", "EXECUTE"},
            "reports": {"CREATE", "READ", "EXPORT"},
            "teams": {"CREATE", "READ", "UPDATE", "MANAGE"},
            "messages": {"CREATE", "READ", "DELETE"},
            "worklogs": {"CREATE", "READ", "UPDATE", "APPROVE"},
        },
        "TeamLead": {
            "projects": {"READ"},
            "tasks": {"CREATE", "READ", "UPDATE", "APPROVE"},
            "users": {"READ"},
            "agents": {"READ", "EXECUTE"},
            "reports": {"READ"},
            "teams": {"READ", "UPDATE"},
            "messages": {"CREATE", "READ"},
            "worklogs": {"CREATE", "READ", "UPDATE", "APPROVE"},
        },
        "Developer": {
            "projects": {"READ"},
            "tasks": {"CREATE", "READ", "UPDATE"},
            "agents": {"READ", "EXECUTE"},
            "reports": {"READ"},
            "teams": {"READ"},
            "messages": {"CREATE", "READ"},
            "worklogs": {"CREATE", "READ", "UPDATE"},
        },
        "Viewer": {
            "projects": {"READ"},
            "tasks": {"READ"},
            "reports": {"READ"},
            "teams": {"READ"},
            "messages": {"READ"},
        },
        "Guest": {
            "projects": {"READ"},
            "tasks": {"READ"},
        },
    }
    
    async def execute(self, db: AsyncSession, **kwargs) -> dict:
        """
        Execute role seeding.
        
        Args:
            db: Database session
            
        Returns:
            dict with seeding results
        """
        self.output.header("Seeding System Roles")
        
        results = {
            "roles_created": 0,
            "roles_updated": 0,
            "permissions_assigned": 0,
            "errors": [],
        }
        
        # Step 1: Check for permissions
        self.output.info("Checking for existing permissions...")
        stmt = select(Permission).where(Permission.is_active == True)
        result = await db.execute(stmt)
        permissions = list(result.scalars().all())
        
        if not permissions:
            self.output.warning("No permissions found!")
            self.output.info("Please run 'python manage.py seed_permissions' first")
            results["errors"].append("No permissions found - run seed_permissions first")
            return results
        
        self.output.success(f"Found {len(permissions)} permissions")
        
        # Build permission lookup
        permission_lookup = {
            (p.resource, p.action.value): p 
            for p in permissions
        }
        
        # Step 2: Create roles
        self.output.info("Creating system roles...")
        
        for role_name, role_config in self.DEFAULT_ROLES.items():
            stmt = select(Role).where(Role.name == role_name)
            result = await db.execute(stmt)
            role = result.scalars().first()
            
            if not role:
                role = Role(
                    name=role_name,
                    description=role_config["description"],
                    is_system=role_config["is_system"],
                    is_active=True,
                )
                db.add(role)
                results["roles_created"] += 1
                self.output.bullet(f"Created: {role_name}")
            else:
                # Update description if needed
                if role.description != role_config["description"]:
                    role.description = role_config["description"]
                    results["roles_updated"] += 1
                self.logger.debug(f"Role exists: {role_name}")
        
        await db.flush()
        
        # Step 3: Assign permissions
        self.output.info("Assigning permissions to roles...")
        
        for role_name, resource_permissions in self.ROLE_PERMISSIONS.items():
            stmt = select(Role).where(Role.name == role_name)
            result = await db.execute(stmt)
            role = result.scalars().first()
            
            if not role:
                self.output.warning(f"Role not found: {role_name}")
                continue
            
            # Get current permissions
            current_perms = set((p.resource, p.action.value) for p in role.permissions)
            
            # Assign new permissions
            for resource, actions in resource_permissions.items():
                for action in actions:
                    perm_key = (resource, action)
                    
                    if perm_key in current_perms:
                        continue
                    
                    permission = permission_lookup.get(perm_key)
                    if permission and permission not in role.permissions:
                        role.permissions.append(permission)
                        results["permissions_assigned"] += 1
                        self.logger.debug(f"Assigned {resource}.{action} to {role_name}")
        
        await db.flush()
        
        # Summary
        self.output.divider()
        self.output.table_row("Roles Created", str(results["roles_created"]))
        self.output.table_row("Roles Updated", str(results["roles_updated"]))
        self.output.table_row("Permissions Assigned", str(results["permissions_assigned"]))
        self.output.divider()
        
        if results["errors"]:
            for error in results["errors"]:
                self.output.error(error)
        elif results["roles_created"] > 0 or results["permissions_assigned"] > 0:
            self.output.success("Role seeding completed successfully!")
        else:
            self.output.info("All roles already configured correctly")
        
        return results


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

async def seed_default_roles(db: AsyncSession) -> dict:
    """
    Convenience function to seed roles without instantiating command.
    
    Usage:
        async with get_db() as db:
            results = await seed_default_roles(db)
    """
    command = SeedRolesCommand()
    return await command.execute(db)
