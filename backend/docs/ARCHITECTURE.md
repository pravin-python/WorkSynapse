# WorkSynapse Enterprise SaaS Backend Architecture

## Overview

WorkSynapse is an enterprise-grade SaaS platform for project management, collaboration, and AI-powered automation. This document describes the complete backend data architecture implemented following enterprise security standards.

## Tech Stack

| Component | Technology |
|-----------|------------|
| **Language** | Python 3.11+ |
| **Framework** | FastAPI |
| **ORM** | SQLAlchemy 2.0 (async) |
| **Database** | PostgreSQL 15+ |
| **Migrations** | Alembic |
| **Authentication** | JWT + bcrypt |
| **Async Driver** | asyncpg |
| **Validation** | Pydantic v2 |

## Security Standards

- **OWASP Top 10** compliance
- **SQL Injection Protection** via parameterized queries (SQLAlchemy ORM)
- **RBAC** (Role-Based Access Control) with granular permissions
- **Audit Logging** for all write operations and security events
- **Input Validation** with Pydantic schemas
- **Password Security** using bcrypt with strength requirements
- **JWT Authentication** with refresh tokens
- **Session Management** with device tracking and revocation

---

## Data Models

### 1. User & Authentication System

**Location:** `app/models/user/model.py`

| Model | Purpose |
|-------|---------|
| `User` | Core user account with MFA, lockout, and status tracking |
| `Role` | Named roles (Admin, Manager, Developer, etc.) |
| `Permission` | Granular permissions (resource + action) |
| `Session` | Active login sessions with device info |
| `LoginHistory` | Record of all login attempts |

**Security Features:**

- Password hashing with bcrypt
- Account lockout after failed attempts
- MFA support (TOTP)
- Session tracking with IP and User-Agent
- Email verification workflow

**RBAC Structure:**

```
User -> UserRoles -> Role -> RolePermissions -> Permission
                                                  |
                                          (resource, action)
```

### 2. Project Management

**Location:** `app/models/project/model.py`

| Model | Purpose |
|-------|---------|
| `Project` | Container for work with ownership and visibility |
| `ProjectMember` | User membership with project-specific roles |
| `Board` | Kanban board configuration |
| `BoardColumn` | Columns within boards |
| `Sprint` | Time-boxed work iterations |
| `Milestone` | Project milestones and deadlines |

### 3. Task Management

**Location:** `app/models/task/model.py`

| Model | Purpose |
|-------|---------|
| `Task` | Work items with status, priority, assignment |
| `TaskDependency` | Dependencies between tasks |
| `Label` | Color-coded labels for categorization |
| `TaskComment` | Threaded comments on tasks |
| `TaskAttachment` | File attachments |
| `TimeLog` | Time tracking entries |

**Special Features:**

- AI-generated task tracking (`is_ai_generated`, `ai_generating_agent_id`)
- Task dependencies with types (blocks, blocked_by, etc.)
- Subtask hierarchy

### 4. Chat System

**Location:** `app/models/chat/model.py`

| Model | Purpose |
|-------|---------|
| `Channel` | Chat rooms (public, private, direct, project) |
| `Message` | Messages with threading support |
| `MessageReaction` | Emoji reactions |
| `MessageFile` | File attachments |
| `ReadReceipt` | Read tracking |
| `PinnedMessage` | Pinned important messages |

### 5. Notes System

**Location:** `app/models/note/model.py`

| Model | Purpose |
|-------|---------|
| `Note` | Rich text notes with visibility controls |
| `NoteFolder` | Hierarchical organization |
| `NoteShare` | Sharing with users/projects |
| `NoteVersion` | Version history |
| `NoteTagDefinition` | Custom tag definitions |
| `NoteComment` | Inline comments with anchors |

### 6. AI Agent Governance System ⚡

**Location:** `app/models/agent/model.py`

This is the **critical audit system** for AI operations.

| Model | Purpose |
|-------|---------|
| `Agent` | AI agent configuration (LLM, prompts, goals) |
| `AgentUserPermission` | Per-user agent access |
| `AgentTool` | Registered tools agents can use |
| `AgentSession` | Conversation sessions |
| `AgentMessage` | Individual messages with token counts |
| `AgentCall` | **Complete LLM API call logs** |
| `AgentAction` | **Complete action audit trail** |
| `AgentTask` | AI-generated tasks |
| `AgentCostLog` | Daily cost aggregation |

**Audit Capabilities:**

- ✅ Every LLM API call logged (prompts, responses, tokens)
- ✅ Every tool usage logged with inputs/outputs
- ✅ Token consumption tracked per call
- ✅ Cost calculated and aggregated
- ✅ Action approvals and rejections recorded
- ✅ Agent configurations versioned

### 7. Work Tracking & Audit Logs

**Location:** `app/models/worklog/model.py`

| Model | Purpose |
|-------|---------|
| `WorkLog` | Manual time entries |
| `ActivityLog` | **Complete audit trail for all actions** |
| `AppUsage` | Application usage tracking |
| `IdlePeriod` | Idle time detection |
| `ProductivitySummary` | Daily/weekly summaries |
| `SecurityAuditLog` | **Security events and incidents** |

---

## Services

### Base CRUD Service

**Location:** `app/services/base.py`

```python
class SecureCRUDBase(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    """
    Enhanced CRUD with:
    - SQL injection protection (parameterized queries)
    - Soft delete support
    - Audit logging
    - Pagination with max limits
    - Search with ILIKE
    """
```

### User Service

**Location:** `app/services/user.py`

- Password hashing with bcrypt
- Authentication with lockout protection
- Login history recording
- Password change with current password verification
- Permission checking

### Agent Service

**Location:** `app/services/agent.py`

- Agent lifecycle management
- Session creation and tracking
- **LLM call logging** (every API call)
- **Token/cost calculation**
- **Action tracking**
- Cost analytics and reporting

---

## Security Middleware

**Location:** `app/middleware/security.py`

### Authentication

```python
@router.get("/protected")
async def protected_route(
    current_user: User = Depends(get_current_user)
):
    ...
```

### RBAC Decorators

```python
@router.delete("/projects/{id}")
@require_permission("projects", PermissionAction.DELETE)
async def delete_project(...):
    ...

@router.post("/admin/users")
@require_roles("ADMIN", "SUPER_ADMIN")
async def admin_action(...):
    ...
```

### Input Sanitization

```python
class InputSanitizer:
    - sanitize_string()  # XSS protection
    - sanitize_email()   # Email validation
    - sanitize_url()     # URL validation

class SQLInjectionProtection:
    - is_safe_input()    # Detect SQL keywords
    - sanitize_identifier()  # Table/column names
```

### Audit Logging

```python
await AuditLogger.log_activity(
    db,
    user_id=current_user.id,
    activity_type=ActivityType.UPDATE,
    resource_type="task",
    resource_id=task.id,
    action="task.status_change",
    old_values={"status": "TODO"},
    new_values={"status": "IN_PROGRESS"},
)
```

---

## Validation Schemas

**Location:** `app/schemas/validation.py`

All API inputs are validated with Pydantic:

- **Length limits** on all string fields
- **Regex validation** for emails, URLs, slugs
- **Custom validators** for passwords, usernames
- **Date validation** (end date > start date)
- **Context size limits** for AI inputs

---

## Testing

**Location:** `app/tests/test_security.py`

Test coverage for:

- ✅ SQL injection detection
- ✅ XSS sanitization
- ✅ Password validation
- ✅ RBAC permissions
- ✅ JWT token handling
- ✅ Prompt injection detection
- ✅ Audit logging

Run tests:

```bash
pytest app/tests/test_security.py -v
```

---

## Alembic Migrations

**Configuration:** `alembic.ini` + `alembic/env.py`

Generate migrations:

```bash
alembic revision --autogenerate -m "Initial models"
```

Apply migrations:

```bash
alembic upgrade head
```

---

## Directory Structure

```
backend/
├── alembic/
│   ├── versions/           # Migration scripts
│   ├── env.py              # Alembic environment
│   └── script.py.mako      # Migration template
├── app/
│   ├── agents/
│   │   └── security.py     # AI security (prompt injection, etc.)
│   ├── core/
│   │   └── config.py       # Configuration settings
│   ├── database/
│   │   └── session.py      # Database connection
│   ├── middleware/
│   │   ├── __init__.py
│   │   └── security.py     # Auth, RBAC, audit, sanitization
│   ├── models/
│   │   ├── __init__.py     # Model imports
│   │   ├── base.py         # Base model with soft delete
│   │   ├── user/model.py   # User, Role, Permission, Session
│   │   ├── project/model.py # Project, Sprint, Milestone
│   │   ├── task/model.py   # Task, Dependencies, Comments
│   │   ├── chat/model.py   # Channel, Message, Reactions
│   │   ├── note/model.py   # Note, Folder, Sharing
│   │   ├── agent/model.py  # AI Agent Governance
│   │   └── worklog/model.py # Work tracking, Audit logs
│   ├── schemas/
│   │   ├── __init__.py
│   │   └── validation.py   # Pydantic schemas
│   ├── services/
│   │   ├── __init__.py
│   │   ├── base.py         # SecureCRUDBase
│   │   ├── user.py         # UserService
│   │   └── agent.py        # AgentService
│   └── tests/
│       └── test_security.py # Security tests
├── alembic.ini             # Alembic configuration
└── requirements.txt        # Dependencies
```

---

## Environment Variables

Required environment variables (see `.env.example`):

```env
# Security (REQUIRED)
SECRET_KEY=your-very-secure-random-secret-key
SERVICE_API_KEY=your-service-api-key

# Database (REQUIRED)
POSTGRES_USER=worksynapse
POSTGRES_PASSWORD=your-secure-password
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=worksynapse

# Optional
DEBUG=false
ENVIRONMENT=development
LOG_LEVEL=INFO
```

---

## Next Steps

1. **Generate Alembic Migration**

   ```bash
   python manage.py init
   alembic revision --autogenerate -m "Initial enterprise schema"
   alembic upgrade head
   python manage.py create-admin

   python manage.py create-admin -e admin2@example.com -u admin2 -p Admin@123 --superuser
   uvicorn app.main:app --port 8000 --reload
   ```

2. **Create API Routers**
   - `app/api/v1/users.py`
   - `app/api/v1/projects.py`
   - `app/api/v1/tasks.py`
   - `app/api/v1/agents.py`

3. **Add Background Tasks**
   - Cost aggregation cron
   - Session cleanup cron
   - Audit log archival

4. **Deploy**
   - Docker + Kubernetes
   - PostgreSQL HA cluster
   - Redis for caching/rate limiting

---

## Security Checklist

- [x] SQL Injection Protection (ORM parameterized queries)
- [x] XSS Prevention (input sanitization)
- [x] CSRF Protection (stateless JWT)
- [x] Password Hashing (bcrypt)
- [x] RBAC Implementation
- [x] Audit Logging
- [x] Session Management
- [x] Account Lockout
- [x] Input Validation
- [x] AI Safety (prompt injection detection)
- [x] Cost Tracking (AI governance)
- [ ] Rate Limiting (Redis-based) - implement
- [ ] WAF Integration - infrastructure
- [ ] Penetration Testing - before production

---

*Architecture designed for enterprise security, OWASP compliance, and complete AI governance auditability.*
