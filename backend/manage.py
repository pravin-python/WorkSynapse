#!/usr/bin/env python
"""
WorkSynapse Management CLI
===========================
Professional command-line interface for administrative operations.

Commands:
- init           : Initialize system (permissions + roles)
- seed_permissions: Seed default system permissions
- seed_roles     : Seed default system roles with permissions
- manage_roles   : Manage roles and permissions
- create_admin   : Create admin/superuser account
- add_permission : Add permission to a role
- remove_permission: Remove permission from a role
- list_roles     : List all roles and their permissions
- list_permissions: List all available permissions

Usage:
    python manage.py <command> [options]

Examples:
    python manage.py init
    python manage.py create_admin --email admin@worksynapse.com --username admin --password SecurePass123!
    python manage.py add_permission --role Admin --permission agents.MANAGE
    python manage.py list_roles
"""

import sys
import asyncio
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import sessionmaker

from commands.seed_permissions import SeedPermissionsCommand
from commands.seed_roles import SeedRolesCommand
from commands.manage_roles import ManageRolesCommand, AddPermissionCommand, RemovePermissionCommand
from commands.create_admin import CreateAdminCommand
try:
    from app.infrastructure.database import engine
except ImportError:
    from app.database.session import engine
from app.models.user.model import Role, Permission

# Initialize Typer app
app = typer.Typer(
    name="WorkSynapse CLI",
    help="Professional management CLI for WorkSynapse administrative operations.",
    add_completion=False
)

console = Console()


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def print_banner():
    """Print the WorkSynapse CLI banner."""
    banner = """
╔═══════════════════════════════════════════════════════════════╗
║                    🚀 WorkSynapse CLI                         ║
║             Admin Management Command System                   ║
╚═══════════════════════════════════════════════════════════════╝
    """
    console.print(banner, style="bold cyan")


from contextlib import asynccontextmanager

@asynccontextmanager
async def get_db_session():
    """Create a database session with proper cleanup."""
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    session = async_session()
    try:
        yield session
        await session.commit()
    except Exception:
        await session.rollback()
        raise
    finally:
        await session.close()


# =============================================================================
# COMMANDS
# =============================================================================

@app.command()
def init():
    """
    🚀 Initialize the system with default permissions and roles.
    
    This command runs:
    1. seed_permissions - Creates all default system permissions
    2. seed_roles - Creates all default roles with proper permissions
    
    This is the recommended first command to run after deployment.
    """
    print_banner()
    console.print("[bold blue]Initializing WorkSynapse system...[/bold blue]\n")
    
    async def _init_system():
        """Run both seed commands within a single event loop and database session."""
        from app.infrastructure.database import engine, AsyncSessionLocal
        
        try:
            # Ensure clean slate before starting
            await engine.dispose()

            # Step 1: Seed permissions
            console.print("[bold]Step 1/2: Seeding permissions...[/bold]")
            perm_cmd = SeedPermissionsCommand()
            await perm_cmd.run_async()
            
            # Reset pool to prevent event loop mismatch errors between commands
            await engine.dispose()

            # Step 2: Seed roles (same event loop, fresh session)
            console.print("\n[bold]Step 2/2: Seeding roles...[/bold]")
            roles_cmd = SeedRolesCommand()
            await roles_cmd.run_async()
            
            console.print("\n[bold green]✅ System initialization complete![/bold green]")
            console.print("[dim]You can now create admin users with 'python manage.py create_admin'[/dim]")
            
        finally:
            # Properly dispose of connection pool at the end
            await engine.dispose()
    
    # Windows-specific event loop policy
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    
    try:
        asyncio.run(_init_system())
    except KeyboardInterrupt:
        console.print("[yellow]⚠️  Command cancelled by user.[/yellow]")
        raise typer.Exit(code=130)
    except Exception as e:
        console.print(f"[bold red]❌ Initialization failed: {e}[/bold red]")
        raise typer.Exit(code=1)


@app.command()
def seed_permissions():
    """
    🔑 Seed default permissions into the database.
    
    Creates all system permissions for RBAC. This command is idempotent -
    running it multiple times will not create duplicates.
    
    Permissions cover: projects, tasks, users, agents, reports, teams, 
    messages, roles, settings, worklogs, api_keys, audit_logs
    """
    print_banner()
    console.print("[bold blue]Seeding system permissions...[/bold blue]\n")
    
    try:
        cmd = SeedPermissionsCommand()
        cmd.run()
    except Exception as e:
        console.print(f"[bold red]❌ Failed to seed permissions: {e}[/bold red]")
        raise typer.Exit(code=1)


@app.command()
def manage_roles():
    """
    👥 Create and configure default system roles.
    
    Creates default roles (SuperAdmin, Admin, Manager, TeamLead, Developer, 
    Viewer, Guest) and assigns appropriate permissions based on role level.
    
    This command is idempotent - safe to run multiple times.
    """
    print_banner()
    console.print("[bold blue]Managing system roles...[/bold blue]\n")
    
    try:
        cmd = ManageRolesCommand()
        cmd.run()
    except Exception as e:
        console.print(f"[bold red]❌ Failed to manage roles: {e}[/bold red]")
        raise typer.Exit(code=1)


@app.command()
def seed_roles():
    """
    👥 Seed default system roles with permissions.
    
    Creates default roles (SuperAdmin, Admin, Manager, TeamLead, Developer, 
    Viewer, Guest) and assigns appropriate permissions based on role level.
    
    This command is idempotent - safe to run multiple times.
    
    Note: Run seed_permissions first to ensure all permissions exist.
    """
    print_banner()
    console.print("[bold blue]Seeding system roles...[/bold blue]\n")
    
    try:
        cmd = SeedRolesCommand()
        cmd.run()
    except Exception as e:
        console.print(f"[bold red]❌ Failed to seed roles: {e}[/bold red]")
        raise typer.Exit(code=1)


@app.command()
def create_admin(
    email: str = typer.Option(..., "--email", "-e", help="Admin email address"),
    username: str = typer.Option(..., "--username", "-u", help="Admin username"),
    password: str = typer.Option(..., "--password", "-p", help="Admin password (min 8 chars, mixed case, number, special char)"),
    full_name: str = typer.Option("System Administrator", "--name", "-n", help="Full display name"),
    superuser: bool = typer.Option(False, "--superuser", "-s", help="Create as Super Admin with full system access")
):
    """
    🧑‍💼 Create a new admin or superuser account.
    
    Creates an admin user with proper role assignment. Passwords are
    securely hashed using bcrypt/argon2. The command is idempotent -
    it will skip if the user already exists.
    
    Password Requirements:
    - Minimum 8 characters
    - At least one uppercase letter
    - At least one lowercase letter
    - At least one digit
    - At least one special character (!@#$%^&*(),.?":{}|<>)
    
    Examples:
        python manage.py create_admin --email admin@example.com --username admin --password SecurePass123!
        python manage.py create_admin -e super@example.com -u superadmin -p SecurePass123! --superuser
    """
    print_banner()
    console.print(f"[bold blue]Creating {'Super Admin' if superuser else 'Admin'} user...[/bold blue]\n")
    
    try:
        cmd = CreateAdminCommand()
        cmd.run(
            email=email,
            username=username,
            password=password,
            full_name=full_name,
            superuser=superuser
        )
    except Exception as e:
        console.print(f"[bold red]❌ Failed to create admin: {e}[/bold red]")
        raise typer.Exit(code=1)


@app.command()
def add_permission(
    role: str = typer.Option(..., "--role", "-r", help="Role name (e.g., Admin, Manager)"),
    permission: str = typer.Option(..., "--permission", "-p", help="Permission in format resource.ACTION (e.g., agents.MANAGE)")
):
    """
    ➕ Add a permission to a role.
    
    Dynamically adds a specific permission to an existing role.
    
    Permission Format: resource.ACTION
    
    Available Actions: CREATE, READ, UPDATE, DELETE, MANAGE, EXECUTE, EXPORT, APPROVE
    
    Examples:
        python manage.py add_permission --role Admin --permission agents.MANAGE
        python manage.py add_permission -r Manager -p reports.EXPORT
    """
    print_banner()
    console.print(f"[bold blue]Adding permission '{permission}' to role '{role}'...[/bold blue]\n")
    
    try:
        cmd = ManageRolesCommand()
        cmd.run(role_name=role, add_permission=permission)
    except Exception as e:
        console.print(f"[bold red]❌ Failed to add permission: {e}[/bold red]")
        raise typer.Exit(code=1)


@app.command()
def remove_permission(
    role: str = typer.Option(..., "--role", "-r", help="Role name (e.g., Admin, Manager)"),
    permission: str = typer.Option(..., "--permission", "-p", help="Permission in format resource.ACTION (e.g., projects.DELETE)")
):
    """
    ➖ Remove a permission from a role.
    
    Dynamically removes a specific permission from an existing role.
    
    Examples:
        python manage.py remove_permission --role Developer --permission projects.DELETE
        python manage.py remove_permission -r Viewer -p tasks.UPDATE
    """
    print_banner()
    console.print(f"[bold blue]Removing permission '{permission}' from role '{role}'...[/bold blue]\n")
    
    try:
        cmd = ManageRolesCommand()
        cmd.run(role_name=role, remove_permission=permission)
    except Exception as e:
        console.print(f"[bold red]❌ Failed to remove permission: {e}[/bold red]")
        raise typer.Exit(code=1)


@app.command()
def list_roles():
    """
    📋 List all roles and their assigned permissions.
    
    Displays a table of all system roles with their permissions count
    and detailed permission lists.
    """
    print_banner()
    console.print("[bold blue]Listing all system roles...[/bold blue]\n")
    
    async def _list_roles():
        async with get_db_session() as db:
            stmt = select(Role).order_by(Role.id)
            result = await db.execute(stmt)
            roles = result.scalars().all()
            
            if not roles:
                console.print("[yellow]No roles found. Run 'python manage.py manage-roles' first.[/yellow]")
                return
            
            # Create table
            table = Table(title="System Roles", show_header=True, header_style="bold cyan")
            table.add_column("ID", style="dim", width=6)
            table.add_column("Role Name", style="bold")
            table.add_column("Description", width=40)
            table.add_column("System", justify="center")
            table.add_column("Permissions", justify="right")
            
            for role in roles:
                table.add_row(
                    str(role.id),
                    role.name,
                    role.description or "-",
                    "✅" if role.is_system else "❌",
                    str(len(role.permissions))
                )
            
            console.print(table)
            
            # Show detailed permissions for each role
            console.print("\n[bold]Detailed Permissions:[/bold]")
            for role in roles:
                if role.permissions:
                    perms = ", ".join(sorted(f"{p.resource}.{p.action.value}" for p in role.permissions))
                    console.print(Panel(perms, title=f"[bold]{role.name}[/bold]", border_style="blue"))
    
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    
    try:
        asyncio.run(_list_roles())
    except Exception as e:
        console.print(f"[bold red]❌ Failed to list roles: {e}[/bold red]")
        raise typer.Exit(code=1)


@app.command()
def list_permissions():
    """
    🔐 List all available system permissions.
    
    Displays a table of all permissions that can be assigned to roles,
    grouped by resource.
    """
    print_banner()
    console.print("[bold blue]Listing all system permissions...[/bold blue]\n")
    
    async def _list_permissions():
        async with get_db_session() as db:
            stmt = select(Permission).order_by(Permission.resource, Permission.action)
            result = await db.execute(stmt)
            permissions = result.scalars().all()
            
            if not permissions:
                console.print("[yellow]No permissions found. Run 'python manage.py seed-permissions' first.[/yellow]")
                return
            
            # Group by resource
            resources = {}
            for perm in permissions:
                if perm.resource not in resources:
                    resources[perm.resource] = []
                resources[perm.resource].append(perm)
            
            # Create table
            table = Table(title="System Permissions", show_header=True, header_style="bold cyan")
            table.add_column("Resource", style="bold")
            table.add_column("Action", style="green")
            table.add_column("Description")
            table.add_column("Active", justify="center")
            
            for resource in sorted(resources.keys()):
                for i, perm in enumerate(resources[resource]):
                    table.add_row(
                        resource if i == 0 else "",
                        perm.action.value,
                        perm.description or "-",
                        "✅" if perm.is_active else "❌"
                    )
            
            console.print(table)
            console.print(f"\n[dim]Total: {len(permissions)} permissions across {len(resources)} resources[/dim]")
    
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    
    try:
        asyncio.run(_list_permissions())
    except Exception as e:
        console.print(f"[bold red]❌ Failed to list permissions: {e}[/bold red]")
        raise typer.Exit(code=1)


@app.command()
def version():
    """
    📌 Display version information.
    """
    console.print(Panel.fit(
        "[bold cyan]WorkSynapse CLI[/bold cyan]\n"
        "[dim]Version: 1.0.0[/dim]\n"
        "[dim]Admin Management Command System[/dim]",
        border_style="cyan"
    ))


# =============================================================================
# MAIN ENTRY POINT
# =============================================================================

if __name__ == "__main__":
    app()
