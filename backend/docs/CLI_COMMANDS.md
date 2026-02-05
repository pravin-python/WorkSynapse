# 🚀 WorkSynapse CLI Commands Reference

This document provides a comprehensive list of administrative commands available through `manage.py`.

## 📌 General Commands

### `init`

Initialize the system with default permissions and roles. This is the recommended first command to run after deployment.

- **Workflow**: Runs `seed-permissions` followed by `seed-roles`.
- **Usage**:

  ```bash
  python manage.py init
  ```

### `version`

Display the current version of the WorkSynapse CLI.

- **Usage**:

  ```bash
  python manage.py version
  ```

---

## 🔐 Authentication & User Management

### `create-admin`

Create a new admin or superuser account with secure password hashing.

- **Options**:
  - `-e, --email`: Admin email address (Required)
  - `-u, --username`: Admin username (Required)
  - `-p, --password`: Admin password (Required, min 8 chars, needs upper, lower, digit, special)
  - `-n, --name`: Full display name (Default: "System Administrator")
  - `-s, --superuser`: Flag to create as a Super Admin with full system access
- **Usage**:

  ```bash
  python manage.py create-admin --email admin@example.com --username admin --password SecurePass123! --superuser
  ```

---

## 👥 Role & Permission Management

### `seed-permissions`

Seed all default system permissions into the database. This command is idempotent.

- **Resources covered**: projects, tasks, users, agents, reports, teams, messages, roles, settings, worklogs, api_keys, audit_logs.
- **Usage**:

  ```bash
  python manage.py seed-permissions
  ```

### `seed-roles`

Seed default system roles (SuperAdmin, Admin, Manager, etc.) and assign their standard permissions.

- **Note**: Run `seed-permissions` before this command.
- **Usage**:

  ```bash
  python manage.py seed-roles
  ```

### `list-roles`

Display a detailed table of all roles, their descriptions, system status, and permission counts.

- **Usage**:

  ```bash
  python manage.py list-roles
  ```

### `list-permissions`

List all available permissions in the system, grouped by resource.

- **Usage**:

  ```bash
  python manage.py list-permissions
  ```

### `add-permission`

Dynamically add a specific permission to an existing role.

- **Options**:
  - `-r, --role`: Name of the role (e.g., Admin, Manager)
  - `-p, --permission`: Permission string in `resource.ACTION` format
- **Usage**:

  ```bash
  python manage.py add-permission --role Developer --permission agents.EXECUTE
  ```

### `remove-permission`

Dynamically remove a specific permission from an existing role.

- **Options**:
  - `-r, --role`: Name of the role
  - `-p, --permission`: Permission string in `resource.ACTION` format
- **Usage**:

  ```bash
  python manage.py remove-permission --role Viewer --permission tasks.UPDATE
  ```

---

## 🛠️ System Maintenance

### `manage-roles`

A versatile command for initializing default roles or modifying permissions. (Similar to `seed-roles` but can be used with flags).

- **Usage**:

  ```bash
  python manage.py manage-roles
  ```

---

## 💡 Pro Tips

- **Hyphens vs Underscores**: Typer CLI automatically converts function names like `create_admin` to CLI commands with hyphens like `create-admin`.
- **Idempotency**: All seeding commands are safe to run multiple times. They will not create duplicate entries.
- **Help**: You can always append `--help` to any command to see its documentation.

  ```bash
  python manage.py create-admin --help
  ```
