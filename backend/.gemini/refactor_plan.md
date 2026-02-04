# WorkSynapse Enterprise Backend Refactor Plan

## Current Structure Analysis

### Existing Directories:
- `app/agents/` - Agent logic (orchestrator, dev_assistant, productivity, etc.)
- `app/api/v1/` - API routers and endpoints
- `app/commands/` - Management commands (already partially implemented)
- `app/core/` - Config, security, logging, celery
- `app/database/` - Database session
- `app/middleware/` - Security and anti-replay middleware
- `app/models/` - SQLAlchemy models by domain
- `app/schemas/` - Pydantic schemas
- `app/services/` - Business logic services
- `app/utils/` - Utility functions
- `app/worker/` - Celery workers

### Issues Identified:
1. Security logic scattered: `app/core/security.py`, `app/middleware/security.py`, `app/agents/security.py`, `app/agents/orchestrator/security.py`
2. Agent logic duplicated: Individual agent folders + orchestrator
3. Middleware outside core
4. No `domain/` layer for clean architecture
5. No `infrastructure/` layer for external services
6. Commands at wrong level (should be at backend root)

---

## Target Architecture

```
backend/
├── app/
│   ├── api/
│   │   ├── v1/
│   │   │   ├── endpoints/           # Endpoint implementations
│   │   │   ├── routers/             # Route definitions
│   │   │   └── api_router.py        # Main API router
│   │   └── deps.py                  # API dependencies
│   │
│   ├── core/
│   │   ├── config.py                # Settings
│   │   ├── security/                # NEW: Consolidated security
│   │   │   ├── __init__.py
│   │   │   ├── auth.py              # JWT, password hashing
│   │   │   ├── middleware.py        # Security middleware
│   │   │   └── antireplay.py        # Anti-replay protection
│   │   ├── logging.py               # Logging config
│   │   └── events.py                # Startup/shutdown events
│   │
│   ├── domain/                      # NEW: Domain layer
│   │   ├── user/
│   │   │   ├── models.py            # User SQLAlchemy models
│   │   │   ├── schemas.py           # User Pydantic schemas
│   │   │   ├── service.py           # User business logic
│   │   │   └── repository.py        # User data access
│   │   ├── project/
│   │   ├── task/
│   │   ├── chat/
│   │   ├── agent/
│   │   ├── worklog/
│   │   └── note/
│   │
│   ├── services/                    # Application services
│   │   ├── auth_service.py          # Authentication
│   │   ├── agent_service.py         # Agent orchestration
│   │   └── websocket_service.py     # WebSocket management
│   │
│   ├── agents/
│   │   └── orchestrator/            # CONSOLIDATED: All agent logic
│   │       ├── __init__.py
│   │       ├── core.py              # Orchestrator core
│   │       ├── factory.py           # Agent factory
│   │       ├── config.py            # Agent configuration
│   │       ├── llm/                 # LLM providers
│   │       ├── memory/              # Memory systems
│   │       ├── tools/               # Tool registry
│   │       └── models/              # Agent data models
│   │
│   ├── infrastructure/              # NEW: External services
│   │   ├── database/
│   │   │   ├── session.py           # DB session factory
│   │   │   └── base.py              # Base model
│   │   ├── redis/
│   │   │   └── client.py            # Redis client
│   │   ├── kafka/
│   │   │   └── producer.py          # Kafka producer
│   │   ├── celery/
│   │   │   ├── app.py               # Celery app
│   │   │   └── tasks.py             # Celery tasks
│   │   └── storage/
│   │       └── s3.py                # S3 storage
│   │
│   ├── utils/
│   └── main.py
│
├── commands/                        # MOVED: Management commands
│   ├── __init__.py
│   ├── base_command.py
│   ├── create_admin.py
│   ├── seed_roles.py
│   └── seed_permissions.py
│
├── alembic/
├── tests/
└── manage.py
```

---

## Refactoring Steps

### Phase 1: Security Consolidation ✅ HIGH PRIORITY
1. Create `app/core/security/` directory
2. Move `app/middleware/security.py` → `app/core/security/middleware.py`
3. Move `app/middleware/antireplay.py` → `app/core/security/antireplay.py`
4. Merge `app/core/security.py` → `app/core/security/auth.py`
5. Update all imports

### Phase 2: Infrastructure Layer ✅ HIGH PRIORITY
1. Create `app/infrastructure/` directory structure
2. Move `app/database/` → `app/infrastructure/database/`
3. Create `app/infrastructure/redis/client.py` from redis service
4. Create `app/infrastructure/kafka/producer.py` from kafka service
5. Move `app/core/celery_app.py` → `app/infrastructure/celery/`
6. Move `app/worker/` → `app/infrastructure/celery/tasks/`

### Phase 3: Domain Layer (Optional - Larger change)
1. Reorganize models, schemas, and services by domain
2. Create repository pattern for data access

### Phase 4: Agent Consolidation
1. Keep `app/agents/orchestrator/` as main agent module
2. Consolidate individual agent logic into orchestrator
3. Remove duplicate agent files

### Phase 5: Commands Restructure
1. Move `app/commands/` → `commands/` (root level)
2. Update `manage.py` imports

---

## Implementation Priority

1. **Security Consolidation** - Most impactful, reduces confusion
2. **Infrastructure Layer** - Clean separation of external services
3. **Move Commands** - Align with target architecture
4. **Agent Cleanup** - Remove duplicates
5. **Domain Layer** - Optional, larger refactor

---

## Files to Create/Move

### New Files:
- `app/core/security/__init__.py`
- `app/core/security/auth.py`
- `app/core/security/middleware.py`
- `app/core/security/antireplay.py`
- `app/infrastructure/__init__.py`
- `app/infrastructure/database/__init__.py`
- `app/infrastructure/redis/__init__.py`
- `app/infrastructure/kafka/__init__.py`
- `app/infrastructure/celery/__init__.py`

### Files to Move:
- `app/middleware/security.py` → `app/core/security/middleware.py`
- `app/middleware/antireplay.py` → `app/core/security/antireplay.py`
- `app/database/session.py` → `app/infrastructure/database/session.py`
- `app/services/redis_service.py` → `app/infrastructure/redis/client.py`
- `app/services/kafka_service.py` → `app/infrastructure/kafka/producer.py`
- `app/core/celery_app.py` → `app/infrastructure/celery/app.py`
- `app/commands/` → `commands/`

### Files to Remove (After Consolidation):
- `app/agents/security.py` (duplicate)
- `app/agents/project_manager.py` (duplicate of folder)
- `app/agents/task_generator.py` (duplicate of folder)
