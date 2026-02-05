# WorkSynapse Backend Enterprise Refactoring Plan

## 📊 Current State Analysis

### Existing Structure

```
backend/
├── app/
│   ├── agents/            # Contains orchestrator + scattered files
│   ├── api/v1/            # ✅ Good structure
│   ├── core/              # Config, logging, security
│   ├── database/          # Legacy location
│   ├── infrastructure/    # ✅ Good structure
│   ├── middleware/        # Security middleware (duplicate)
│   ├── models/            # Flat domain models
│   ├── schemas/           # ✅ Good
│   ├── services/          # ✅ Good
│   ├── utils/             # ✅ Good
│   └── main.py           # ✅ Good
├── commands/             # Management commands
├── manage.py            # ✅ Professional CLI
└── alembic/             # ✅ Migrations
```

### Issues Identified

1. **Security Duplication**: `app/core/security/`, `app/middleware/`, `app/core/security.py`
2. **Commands Duplication**: `commands/` (root) and `app/commands/`
3. **Scattered Agents**: Agent files outside `orchestrator/`
4. **Missing Domain Layer**: No clear domain separation

---

## 🎯 Target Architecture

```
backend/
├── app/
│   ├── api/
│   │   └── v1/
│   │       ├── routers/        # Route handlers by domain
│   │       ├── endpoints/      # WebSocket endpoints
│   │       └── api_router.py   # Central router
│   │
│   ├── core/
│   │   ├── config.py           # Environment config
│   │   ├── security/           # CONSOLIDATED security
│   │   │   ├── __init__.py
│   │   │   ├── auth.py         # Authentication
│   │   │   ├── rbac.py         # Role-based access control
│   │   │   ├── antireplay.py   # Anti-replay protection
│   │   │   ├── middleware.py   # Security middleware
│   │   │   └── utils.py        # Security utilities
│   │   ├── logging.py
│   │   └── exceptions.py       # Custom exceptions
│   │
│   ├── domain/                  # Domain entities
│   │   ├── user/
│   │   ├── project/
│   │   ├── task/
│   │   ├── chat/
│   │   ├── agent/
│   │   └── worklog/
│   │
│   ├── services/               # Business logic
│   │   ├── auth_service.py
│   │   ├── agent_service.py
│   │   ├── project_service.py
│   │   └── websocket_service.py
│   │
│   ├── agents/
│   │   └── orchestrator/       # CONSOLIDATED agent logic
│   │       ├── llm/            # LLM providers
│   │       ├── memory/         # Memory systems
│   │       ├── tools/          # Tool registry
│   │       ├── core.py         # Core orchestrator
│   │       └── factory.py      # Agent factory
│   │
│   ├── infrastructure/
│   │   ├── database/
│   │   ├── redis/
│   │   ├── kafka/
│   │   ├── celery/
│   │   └── storage/
│   │
│   ├── schemas/               # Pydantic schemas
│   ├── utils/                 # Utilities
│   └── main.py
│
├── commands/                   # Management commands
│   ├── __init__.py
│   ├── base_command.py
│   ├── create_admin.py
│   ├── seed_roles.py          # NEW
│   └── seed_permissions.py
│
├── alembic/
├── tests/
└── manage.py
```

---

## 📋 Refactoring Steps

### Phase 1: Consolidate Security Layer

1. Move all security code to `app/core/security/`
2. Create unified security module
3. Update imports throughout codebase

### Phase 2: Consolidate Agent Layer  

1. Move scattered agent files into `app/agents/orchestrator/`
2. Create agent factory pattern
3. Remove duplicate agent logic

### Phase 3: Create Domain Layer

1. Restructure models into domain directories
2. Maintain backward compatibility with imports

### Phase 4: Standardize Commands

1. Remove `app/commands/` (use root `commands/`)
2. Add `seed_roles.py` command
3. Ensure CLI is complete

### Phase 5: Clean Up

1. Remove duplicate files
2. Update all imports
3. Run tests

---

## ✅ Completion Checklist

- [x] Security layer consolidated
  - Created `app/core/security/auth.py` - Authentication utilities
  - Created `app/core/security/rbac.py` - RBAC decorators  
  - Created `app/core/security/deps.py` - Authentication dependencies
  - Created `app/core/security/sanitization.py` - Input validation
  - Created `app/core/security/audit.py` - Audit logging
  - Created `app/core/security/rate_limit.py` - Rate limiting
  - Created `app/core/security/middleware.py` - Security middleware
  - Created `app/core/security/antireplay.py` - Anti-replay protection
  - Consolidated `app/core/security/__init__.py` with all exports

- [x] Domain layer established
  - Created `app/domain/__init__.py`
  - Created `app/domain/user/__init__.py`
  - Created `app/domain/project/__init__.py`
  - Created `app/domain/task/__init__.py`
  - Created `app/domain/chat/__init__.py`
  - Created `app/domain/agent/__init__.py`
  - Created `app/domain/worklog/__init__.py`

- [x] Management commands complete
  - `commands/seed_permissions.py` - Seeds system permissions
  - `commands/seed_roles.py` - Seeds default roles with permissions
  - `commands/manage_roles.py` - Dynamic role/permission management
  - `commands/create_admin.py` - Admin user creation
  - Updated `manage.py` with all commands

- [x] RBAC seeding implemented
  - `seed_roles.py` creates all default roles
  - Assigns proper permissions to each role
  - Idempotent operation (safe to run multiple times)

- [x] Services layer enhanced
  - Created `app/services/auth_service.py`
  - Created `app/services/project_service.py`
  - Created `app/services/websocket_service.py`
  - Updated `app/services/__init__.py` with all exports

- [ ] Agent orchestration centralized (existing structure maintained)
- [ ] All imports updated (backward compatible wrappers in place)
- [ ] Tests passing (requires manual verification)
