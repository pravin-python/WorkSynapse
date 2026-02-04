"""
WorkSynapse Seed Permissions Command
====================================
Command to seed default system permissions into the database.

Features:
- Comprehensive permission set for RBAC
- Idempotent operation (won't create duplicates)
- Transaction-safe batch creation
- Detailed logging and output

Permissions follow the pattern: resource.action
Resources: projects, tasks, users, agents, reports, teams, messages, etc.
Actions: CREATE, READ, UPDATE, DELETE, MANAGE, EXECUTE, EXPORT, APPROVE

Usage:
    python manage.py seed_permissions
"""

from typing import List, Tuple
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from commands.base_command import BaseCommand
from app.models.user.model import Permission, PermissionAction


class SeedPermissionsCommand(BaseCommand):
    """
    Command to seed default system permissions.
    
    This creates a comprehensive set of permissions that cover all
    system resources and actions. The command is idempotent - running
    it multiple times will not create duplicates.
    """
    
    name = "seed_permissions"
    description = "Seed default system permissions into the database"
    
    # Comprehensive permission definitions
    # Format: (resource, action, description)
    DEFAULT_PERMISSIONS: List[Tuple[str, PermissionAction, str]] = [
        # ===== Projects =====
        ("projects", PermissionAction.CREATE, "Create new projects"),
        ("projects", PermissionAction.READ, "View project details"),
        ("projects", PermissionAction.UPDATE, "Update project settings"),
        ("projects", PermissionAction.DELETE, "Delete projects"),
        ("projects", PermissionAction.MANAGE, "Full project management"),
        ("projects", PermissionAction.EXPORT, "Export project data"),
        
        # ===== Tasks =====
        ("tasks", PermissionAction.CREATE, "Create new tasks"),
        ("tasks", PermissionAction.READ, "View task details"),
        ("tasks", PermissionAction.UPDATE, "Update task information"),
        ("tasks", PermissionAction.DELETE, "Delete tasks"),
        ("tasks", PermissionAction.MANAGE, "Full task management"),
        ("tasks", PermissionAction.APPROVE, "Approve task completion"),
        
        # ===== Users =====
        ("users", PermissionAction.CREATE, "Create new users"),
        ("users", PermissionAction.READ, "View user profiles"),
        ("users", PermissionAction.UPDATE, "Update user information"),
        ("users", PermissionAction.DELETE, "Delete user accounts"),
        ("users", PermissionAction.MANAGE, "Full user management including roles"),
        
        # ===== Agents (AI) =====
        ("agents", PermissionAction.CREATE, "Create AI agents"),
        ("agents", PermissionAction.READ, "View agent configurations"),
        ("agents", PermissionAction.UPDATE, "Update agent settings"),
        ("agents", PermissionAction.DELETE, "Delete AI agents"),
        ("agents", PermissionAction.EXECUTE, "Run/execute AI agents"),
        ("agents", PermissionAction.MANAGE, "Full agent management"),
        
        # ===== Reports =====
        ("reports", PermissionAction.CREATE, "Create custom reports"),
        ("reports", PermissionAction.READ, "View system reports"),
        ("reports", PermissionAction.EXPORT, "Export reports to file"),
        ("reports", PermissionAction.MANAGE, "Manage report configurations"),
        
        # ===== Teams =====
        ("teams", PermissionAction.CREATE, "Create new teams"),
        ("teams", PermissionAction.READ, "View team information"),
        ("teams", PermissionAction.UPDATE, "Update team settings"),
        ("teams", PermissionAction.DELETE, "Delete teams"),
        ("teams", PermissionAction.MANAGE, "Full team management"),
        
        # ===== Messages/Chat =====
        ("messages", PermissionAction.CREATE, "Send messages"),
        ("messages", PermissionAction.READ, "Read messages"),
        ("messages", PermissionAction.DELETE, "Delete messages"),
        ("messages", PermissionAction.MANAGE, "Manage all messages"),
        
        # ===== Roles & Permissions (System) =====
        ("roles", PermissionAction.CREATE, "Create new roles"),
        ("roles", PermissionAction.READ, "View role definitions"),
        ("roles", PermissionAction.UPDATE, "Update role permissions"),
        ("roles", PermissionAction.DELETE, "Delete custom roles"),
        ("roles", PermissionAction.MANAGE, "Full role management"),
        
        # ===== Settings =====
        ("settings", PermissionAction.READ, "View system settings"),
        ("settings", PermissionAction.UPDATE, "Update system settings"),
        ("settings", PermissionAction.MANAGE, "Full settings management"),
        
        # ===== Worklogs =====
        ("worklogs", PermissionAction.CREATE, "Log work time"),
        ("worklogs", PermissionAction.READ, "View work logs"),
        ("worklogs", PermissionAction.UPDATE, "Update work logs"),
        ("worklogs", PermissionAction.DELETE, "Delete work logs"),
        ("worklogs", PermissionAction.APPROVE, "Approve work logs"),
        
        # ===== API Keys =====
        ("api_keys", PermissionAction.CREATE, "Create API keys"),
        ("api_keys", PermissionAction.READ, "View API keys"),
        ("api_keys", PermissionAction.DELETE, "Revoke API keys"),
        ("api_keys", PermissionAction.MANAGE, "Manage all API keys"),
        
        # ===== Audit Logs =====
        ("audit_logs", PermissionAction.READ, "View audit logs"),
        ("audit_logs", PermissionAction.EXPORT, "Export audit data"),
    ]
    
    async def execute(self, db: AsyncSession, *args, **kwargs) -> dict:
        """
        Seed all default permissions into the database.
        
        Returns:
            dict with counts of created and existing permissions
        """
        self.output.header("Seeding System Permissions")
        
        created_count = 0
        existing_count = 0
        
        for resource, action, description in self.DEFAULT_PERMISSIONS:
            # Check if permission already exists
            stmt = select(Permission).where(
                Permission.resource == resource,
                Permission.action == action
            )
            result = await db.execute(stmt)
            existing = result.scalars().first()
            
            if existing:
                existing_count += 1
                self.logger.debug(f"Permission exists: {resource}.{action.value}")
            else:
                # Create new permission
                permission = Permission(
                    resource=resource,
                    action=action,
                    description=description,
                    is_active=True
                )
                db.add(permission)
                created_count += 1
                self.output.bullet(f"Created: {resource}.{action.value}")
        
        if created_count > 0:
            await db.flush()
        
        # Output summary
        self.output.divider()
        self.output.table_row("Permissions Created", str(created_count))
        self.output.table_row("Already Existed", str(existing_count))
        self.output.table_row("Total Defined", str(len(self.DEFAULT_PERMISSIONS)))
        self.output.divider()
        
        if created_count > 0:
            self.output.success(f"Successfully seeded {created_count} new permissions")
        else:
            self.output.info("All permissions already exist. Database is up-to-date.")
        
        return {
            "created": created_count,
            "existing": existing_count,
            "total": len(self.DEFAULT_PERMISSIONS)
        }
    
    @classmethod
    def get_permission_resources(cls) -> List[str]:
        """Get list of all unique resources defined in permissions."""
        return list(set(p[0] for p in cls.DEFAULT_PERMISSIONS))
    
    @classmethod
    def get_permission_actions(cls) -> List[str]:
        """Get list of all unique actions defined in permissions."""
        return list(set(p[1].value for p in cls.DEFAULT_PERMISSIONS))
