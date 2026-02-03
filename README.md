<p align="center">
  <img src="assets/logos/logo.png" alt="WorkSynapse Logo" width="200"/>
</p>

<h1 align="center">🧠 WorkSynapse</h1>

<p align="center">
  <strong>AI-Powered Intelligent Company Operating System</strong>
</p>

<p align="center">
  <a href="#features">Features</a> •
  <a href="#architecture">Architecture</a> •
  <a href="#tech-stack">Tech Stack</a> •
  <a href="#quick-start">Quick Start</a> •
  <a href="#api-docs">API Docs</a>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/version-1.0.0-blue.svg" alt="Version"/>
  <img src="https://img.shields.io/badge/license-MIT-green.svg" alt="License"/>
  <img src="https://img.shields.io/badge/PRs-welcome-brightgreen.svg" alt="PRs Welcome"/>
</p>

---

## 🎯 Overview

**WorkSynapse** is a production-grade, full-stack intelligent company operating system designed to revolutionize how teams collaborate, manage projects, and boost productivity. It seamlessly integrates AI-powered agents, real-time communication, project management, and automated time tracking into one unified platform.

### 🌟 What Makes WorkSynapse Unique?

| Feature | Description |
|---------|-------------|
| 🤖 **AI Agents** | Intelligent agents that automate project management, task generation, and developer assistance |
| ⏱️ **Auto Time Tracking** | Desktop app with work detection model for automatic productivity tracking |
| 💬 **Real-time Chat** | Secure WebSocket-based team communication with channels |
| 📊 **Smart Dashboards** | Analytics and insights powered by AI |
| 🔒 **Enterprise Security** | JWT auth, RBAC, rate limiting, and zero-trust architecture |

---

## ✨ Features

### 💬 Company Internal Chat
- Real-time messaging via WebSockets
- Channel-based communication
- Direct messages & group chats
- Message search & history
- File sharing & attachments
- Presence indicators (online/offline)
- @ mentions & notifications

### 📋 Trello-Style Project Boards
- Drag-and-drop Kanban boards
- Custom columns & workflows
- Card labels, checklists, due dates
- Board templates
- Activity timeline
- Board sharing & permissions

### 🎯 Task & Sprint Management
- Sprint planning & tracking
- Backlog management
- Story points & velocity
- Burndown charts
- Task dependencies
- Time estimates vs actuals

### 🤖 AI Project Manager Agents
- **Project Manager Agent**: Creates roadmaps, milestones, and tracks progress
- **Task Generator Agent**: Converts feature descriptions into actionable tasks
- **Dev Assistant Agent**: Answers code questions, suggests fixes, explains logic
- **Productivity Agent**: Analyzes work patterns and provides insights

### 🧠 Smart Task Auto-Assignment
- AI analyzes team skills & workload
- Automatic task distribution
- Balanced workload management
- Skill-based matching
- Priority-aware assignment

### ⏰ Work Detection & Auto Time Tracking
- Desktop activity monitoring
- Automatic timer start/stop
- Application usage tracking
- Idle time detection
- Productivity scoring
- Daily/weekly reports

### 📝 Notes, Sharing & Forwarding
- Rich text editor
- Markdown support
- Note organization (folders/tags)
- Share with team members
- Forward to channels/DMs
- Version history

---

## 🏗️ Architecture

WorkSynapse follows a **Modular Monorepo** architecture combining **Event-Driven** and **Layered** patterns for scalability and maintainability.

```
┌─────────────────────────────────────────────────────────────────┐
│                        CLIENT LAYER                              │
├─────────────────┬─────────────────┬─────────────────────────────┤
│   Web App       │   Desktop App   │    Mobile (Future)          │
│   (React/TS)    │   (Electron)    │                             │
└────────┬────────┴────────┬────────┴─────────────────────────────┘
         │                 │
         ▼                 ▼
┌─────────────────────────────────────────────────────────────────┐
│                      API GATEWAY                                 │
│              (FastAPI + Security Middleware)                     │
│         Rate Limiting │ JWT Auth │ RBAC │ Logging                │
└────────────────────────────┬────────────────────────────────────┘
                             │
         ┌───────────────────┼───────────────────┐
         ▼                   ▼                   ▼
┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐
│   REST API      │ │   WebSocket     │ │   Webhooks      │
│   Endpoints     │ │   Handler       │ │   (GitHub/Jira) │
└────────┬────────┘ └────────┬────────┘ └────────┬────────┘
         │                   │                   │
         └───────────────────┼───────────────────┘
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                     SERVICE LAYER                                │
├─────────────────┬─────────────────┬─────────────────────────────┤
│   User Service  │ Project Service │ Task Service                │
│   Chat Service  │ Agent Service   │ Analytics Service           │
└────────┬────────┴────────┬────────┴─────────────────────────────┘
         │                 │
         ▼                 ▼
┌─────────────────────────────────────────────────────────────────┐
│                    MESSAGE BROKERS                               │
├─────────────────────────────┬───────────────────────────────────┤
│         Kafka               │          RabbitMQ                 │
│   (Event Streaming)         │      (Task Queue/Celery)          │
│   - Chat messages           │      - AI Agent jobs              │
│   - Activity logs           │      - Notifications              │
│   - System events           │      - Background tasks           │
└─────────────────────────────┴───────────────────────────────────┘
         │                                     │
         ▼                                     ▼
┌─────────────────┐                   ┌─────────────────┐
│     Redis       │                   │  Celery Workers │
│  - Caching      │                   │  - AI Agents    │
│  - Sessions     │                   │  - Emails       │
│  - Rate Limits  │                   │  - Analytics    │
│  - Presence     │                   │                 │
└─────────────────┘                   └─────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────────┐
│                     DATA LAYER                                   │
├─────────────────────────────────────────────────────────────────┤
│                    PostgreSQL                                    │
│  Users │ Projects │ Tasks │ Messages │ WorkLogs │ Notes         │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🛠️ Tech Stack

### Backend (`backend/`)
| Technology | Purpose |
|------------|---------|
| **FastAPI** | High-performance async API framework |
| **SQLAlchemy** | Async ORM with PostgreSQL |
| **Pydantic** | Data validation & serialization |
| **Celery** | Distributed task queue |
| **Redis** | Caching, sessions, rate limiting |
| **Kafka** | Event streaming |
| **RabbitMQ** | Message broker for Celery |
| **JWT + OAuth2** | Authentication & authorization |

### Web App (`web/`)
| Technology | Purpose |
|------------|---------|
| **React 18** | UI library |
| **TypeScript** | Type-safe JavaScript |
| **Vite** | Build tool & dev server |
| **Zustand** | State management |
| **React Router** | Client-side routing |
| **Socket.IO** | Real-time communication |
| **Vanilla CSS** | Premium dark mode styling |

### Desktop App (`desktop/`)
| Technology | Purpose |
|------------|---------|
| **Electron** | Cross-platform desktop framework |
| **Python** | Activity detection scripts |
| **TypeScript** | Main & renderer process |

### DevOps (`devops/`)
| Technology | Purpose |
|------------|---------|
| **Docker** | Containerization |
| **Kubernetes** | Orchestration |
| **Prometheus** | Metrics collection |
| **Grafana** | Monitoring dashboards |

---

## 📁 Project Structure

```
worksynapse/
│
├── 📂 assets/                    # Global shared assets
│   ├── logos/                    # Brand logos
│   ├── icons/                    # UI icons
│   ├── illustrations/            # Decorative graphics
│   └── backgrounds/              # Background images
│
├── 📂 backend/                   # FastAPI Backend
│   ├── app/
│   │   ├── api/
│   │   │   ├── v1/
│   │   │   │   ├── routers/      # API endpoints
│   │   │   │   │   ├── auth.py   # Login, register, refresh
│   │   │   │   │   ├── users.py  # User CRUD
│   │   │   │   │   ├── projects.py
│   │   │   │   │   ├── tasks.py
│   │   │   │   │   ├── chat.py
│   │   │   │   │   ├── agents.py
│   │   │   │   │   ├── webhooks.py
│   │   │   │   │   ├── files.py
│   │   │   │   │   ├── notes.py
│   │   │   │   │   └── worklogs.py
│   │   │   │   └── endpoints/
│   │   │   │       └── websockets.py
│   │   │   └── deps.py           # Dependencies (Auth, RBAC)
│   │   │
│   │   ├── core/
│   │   │   ├── config.py         # Environment configuration
│   │   │   ├── security.py       # JWT, password hashing
│   │   │   ├── logging.py        # Structured logging
│   │   │   └── celery_app.py     # Celery configuration
│   │   │
│   │   ├── middleware/
│   │   │   └── security.py       # Security headers, rate limiting
│   │   │
│   │   ├── models/               # SQLAlchemy models
│   │   │   ├── base.py
│   │   │   ├── user/model.py
│   │   │   ├── project/model.py
│   │   │   ├── task/model.py
│   │   │   ├── chat/model.py
│   │   │   └── worklog/model.py
│   │   │
│   │   ├── schemas/              # Pydantic schemas
│   │   │   ├── user.py
│   │   │   ├── project.py
│   │   │   └── task.py
│   │   │
│   │   ├── services/             # Business logic
│   │   │   ├── base.py           # Generic CRUD
│   │   │   ├── user.py
│   │   │   ├── project.py
│   │   │   ├── redis_service.py  # Cache, sessions, locks
│   │   │   ├── kafka_service.py  # Event streaming
│   │   │   └── websocket_manager.py
│   │   │
│   │   ├── agents/               # AI Agents
│   │   │   ├── base.py           # Abstract base class
│   │   │   ├── security.py       # Prompt injection protection
│   │   │   ├── project_manager/
│   │   │   ├── task_generator/
│   │   │   ├── dev_assistant/
│   │   │   └── productivity/
│   │   │
│   │   ├── worker/               # Celery tasks
│   │   │   └── tasks/
│   │   │       ├── agents.py
│   │   │       ├── notifications.py
│   │   │       └── analytics.py
│   │   │
│   │   ├── database/
│   │   │   └── session.py        # Async SQLAlchemy setup
│   │   │
│   │   └── main.py               # FastAPI app entry
│   │
│   ├── Dockerfile
│   ├── requirements.txt
│   └── .env.example
│
├── 📂 web/                       # React Web App
│   ├── src/
│   │   ├── app/                  # App configuration
│   │   ├── features/             # Feature modules
│   │   │   ├── auth/
│   │   │   ├── projects/
│   │   │   ├── tasks/
│   │   │   ├── chat/
│   │   │   ├── notes/
│   │   │   ├── agents/
│   │   │   └── dashboard/
│   │   ├── components/           # Shared UI components
│   │   ├── hooks/                # Custom React hooks
│   │   ├── services/             # API clients
│   │   └── types/                # TypeScript types
│   ├── Dockerfile
│   ├── nginx.conf
│   └── package.json
│
├── 📂 desktop/                   # Electron Desktop App
│   ├── src/
│   │   ├── main/                 # Main process
│   │   ├── renderer/             # Renderer process (UI)
│   │   ├── work-detection/       # Python activity tracking
│   │   │   ├── activity_detector.py
│   │   │   ├── idle_tracker.py
│   │   │   └── app_monitor.py
│   │   └── timer/                # Timer components
│   └── package.json
│
├── 📂 shared-types/              # Shared TypeScript definitions
│   └── models/
│       └── index.ts
│
├── 📂 devops/                    # DevOps configurations
│   ├── k8s/
│   │   ├── backend-deployment.yaml
│   │   ├── celery-deployment.yaml
│   │   ├── database-deployment.yaml
│   │   ├── web-ingress.yaml
│   │   └── config-secrets.yaml
│   └── prometheus.yml
│
├── docker-compose.yml            # Full stack Docker setup
├── .env.example                  # Environment template
├── .gitignore                    # Git ignore rules
└── README.md                     # This file
```

---

## 🔐 Security Features

### API Security
| Feature | Implementation |
|---------|----------------|
| 🔑 **JWT Authentication** | Access + Refresh tokens with rotation |
| 👥 **RBAC** | Role-based access (Admin, Manager, Developer) |
| 🚦 **Rate Limiting** | Redis-backed request throttling |
| 🛡️ **Security Headers** | X-Frame-Options, CSP, HSTS |
| ✅ **Input Validation** | Pydantic schemas for all endpoints |
| 🔒 **Password Hashing** | Argon2 + bcrypt fallback |

### 🔐 Anti-Replay Protection (NEW!)

WorkSynapse implements **Zepto-style one-time API request protection** where every API request can only be used once:

| Feature | Implementation |
|---------|----------------|
| 📝 **HMAC-SHA256 Signatures** | All requests signed with secret key |
| 🎫 **UUID Nonces** | Each request has unique nonce |
| ⏰ **Timestamp Validation** | ±30 second window enforcement |
| 🗄️ **Redis Nonce Store** | 60-second TTL, distributed servers |
| 🚫 **IP Throttling** | Suspicious activity tracking & blocking |

**Required Headers for Protected Endpoints:**
```http
X-API-KEY: your-api-key
X-TIMESTAMP: 1706979600
X-NONCE: 123e4567-e89b-12d3-a456-426614174000
X-SIGNATURE: a1b2c3d4e5f6...
```

**Error Codes:**
| Code | Meaning |
|------|---------|
| 401 | Missing headers or invalid API key |
| 403 | Invalid signature or IP blocked |
| 408 | Timestamp expired |
| 409 | Nonce already used (replay attack) |
| 429 | Rate limit exceeded |

See [`backend/docs/ANTI_REPLAY_SECURITY.md`](backend/docs/ANTI_REPLAY_SECURITY.md) for full documentation.

### Real-time Security
| Feature | Implementation |
|---------|----------------|
| 🔐 **WebSocket Auth** | JWT verification on handshake |
| 📝 **Message Validation** | Size limits, spam detection |
| ⚡ **Rate Limiting** | Per-user message throttling |
| 🔏 **Webhook Verification** | HMAC signature validation |
| 🔄 **Replay Protection** | Idempotency keys + Redis |

### Agent Security
| Feature | Implementation |
|---------|----------------|
| 🛑 **Prompt Injection Detection** | Pattern-based filtering |
| 🔧 **Tool Whitelisting** | Per-agent allowed tools |
| 🧹 **Output Sanitization** | Sensitive data removal |
| 📦 **Context Isolation** | Separate session contexts |

---

## 🚀 Quick Start

### Prerequisites
- Docker & Docker Compose
- Node.js 20+
- Python 3.11+
- Git

### 1️⃣ Clone Repository
```bash
git clone https://github.com/your-org/worksynapse.git
cd worksynapse
```

### 2️⃣ Setup Environment
```bash
# Copy environment template
cp .env.example .env

# Generate secure secrets
openssl rand -hex 32  # For SECRET_KEY
openssl rand -hex 24  # For SERVICE_API_KEY

# Edit .env with your values
nano .env
```

### 3️⃣ Start with Docker
```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f backend
```

### 4️⃣ Access Applications
| Service | URL |
|---------|-----|
| 🌐 Web App | http://localhost:80 |
| 🔌 API Docs | http://localhost:8000/api/v1/docs |
| 🐰 RabbitMQ | http://localhost:15672 |
| 📊 Prometheus | http://localhost:9090 |
| 📈 Grafana | http://localhost:3000 |

---

## 💻 Local Development

### Backend
```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run development server
uvicorn app.main:app --reload --port 8000
```

### Celery Worker
```bash
celery -A app.core.celery_app worker --loglevel=info
```

### Web App
```bash
cd web

# Install dependencies
npm install

# Start dev server
npm run dev
```

### Desktop App
```bash
cd desktop

# Install dependencies
npm install

# Start Electron
npm start
```

---

## 📡 API Endpoints

### Authentication
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/auth/login` | User login |
| POST | `/api/v1/auth/register` | User registration |
| POST | `/api/v1/auth/refresh` | Refresh tokens |
| POST | `/api/v1/auth/logout` | User logout |

### Users
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/users` | List users |
| GET | `/api/v1/users/{id}` | Get user |
| PUT | `/api/v1/users/{id}` | Update user |

### Projects
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/projects` | List projects |
| POST | `/api/v1/projects` | Create project |
| GET | `/api/v1/projects/{id}` | Get project |
| PUT | `/api/v1/projects/{id}` | Update project |
| DELETE | `/api/v1/projects/{id}` | Delete project |

### Tasks
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/tasks` | List tasks |
| POST | `/api/v1/tasks` | Create task |
| GET | `/api/v1/tasks/{id}` | Get task |
| PUT | `/api/v1/tasks/{id}` | Update task |
| DELETE | `/api/v1/tasks/{id}` | Delete task |

### WebSocket
| Endpoint | Description |
|----------|-------------|
| `WS /api/v1/ws/{channel_id}?token=XXX` | Real-time chat |

### Webhooks
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/webhooks/github` | GitHub events |
| POST | `/api/v1/webhooks/jira` | Jira events |

### Health
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Health check |
| GET | `/metrics` | Prometheus metrics |

---

## 🤖 AI Agents

### Project Manager Agent
```python
# Capabilities
- Create project roadmaps
- Generate milestones
- Track progress
- Suggest timeline adjustments
```

### Task Generator Agent
```python
# Capabilities
- Convert features to tasks
- Estimate story points
- Create subtasks
- Generate acceptance criteria
```

### Dev Assistant Agent
```python
# Capabilities
- Answer code questions
- Explain complex logic
- Suggest bug fixes
- Code review assistance
```

### Productivity Agent
```python
# Capabilities
- Analyze work patterns
- Generate productivity reports
- Identify bottlenecks
- Suggest improvements
```

---

## ☸️ Kubernetes Deployment

```bash
# Create namespace
kubectl apply -f devops/k8s/config-secrets.yaml

# Deploy databases
kubectl apply -f devops/k8s/database-deployment.yaml

# Deploy backend
kubectl apply -f devops/k8s/backend-deployment.yaml

# Deploy workers
kubectl apply -f devops/k8s/celery-deployment.yaml

# Deploy frontend & ingress
kubectl apply -f devops/k8s/web-ingress.yaml
```

---

## 📊 Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `SECRET_KEY` | JWT signing key (min 32 chars) | ✅ |
| `SERVICE_API_KEY` | Service-to-service auth | ✅ |
| `POSTGRES_USER` | Database username | ✅ |
| `POSTGRES_PASSWORD` | Database password | ✅ |
| `REDIS_PASSWORD` | Redis password | ✅ |
| `RABBITMQ_PASSWORD` | RabbitMQ password | ✅ |
| `OPENAI_API_KEY` | OpenAI for AI agents | ⚡ |
| `GITHUB_WEBHOOK_SECRET` | GitHub webhook secret | ⚡ |

See `.env.example` for full list.

---

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

<p align="center">
  <strong>Built with ❤️ for Enterprise Teams</strong>
</p>

<p align="center">
  <a href="https://worksynapse.com">Website</a> •
  <a href="https://docs.worksynapse.com">Documentation</a> •
  <a href="https://github.com/your-org/worksynapse/issues">Report Bug</a>
</p>
