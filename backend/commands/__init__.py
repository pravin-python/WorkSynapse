"""
WorkSynapse Management Commands
================================
Professional CLI command system for admin operations.

Available Commands:
- create_admin: Create admin/superuser accounts
- seed_permissions: Initialize system permissions
- seed_roles: Create default system roles with permissions
- manage_roles: Manage roles and role-permission assignments
- init: Bootstrap the entire system (permissions + roles)

Usage:
    python manage.py <command> [options]

Examples:
    python manage.py init
    python manage.py create_admin --email admin@worksynapse.com --username admin --password SecurePass123!
    python manage.py seed_permissions
    python manage.py seed_roles
    python manage.py manage_roles --role Admin --add-permission agents.MANAGE
"""

from .base_command import BaseCommand
from .create_admin import CreateAdminCommand
from .manage_roles import ManageRolesCommand, AddPermissionCommand, RemovePermissionCommand
from .seed_permissions import SeedPermissionsCommand
from .seed_roles import SeedRolesCommand

__all__ = [
    "BaseCommand",
    "CreateAdminCommand",
    "ManageRolesCommand",
    "AddPermissionCommand",
    "RemovePermissionCommand",
    "SeedPermissionsCommand",
    "SeedRolesCommand",
]
