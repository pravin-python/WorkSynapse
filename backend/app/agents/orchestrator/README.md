# Dynamic Agent Platform - Implementation Overview

## Architecture Summary

The WorkSynapse Dynamic Agent Platform is a LangChain + LangGraph-powered multi-agent orchestration system that allows:

- **Frontend Agent Creation**: Agents can be created, configured, and managed through the API
- **Multi-Agent Support**: Multiple agents running simultaneously with isolation
- **Custom System Prompts, Goals, and Tools**: Full customization per agent
- **MCP Connectors**: GitHub, Slack, Teams, Telegram integrations
- **Dynamic LLM Routing**: OpenAI, Ollama, Gemini, Claude, HuggingFace

## Directory Structure

```
backend/app/agents/orchestrator/
├── __init__.py                 # Package exports
├── config.py                   # Configuration (OrchestratorConfig)
├── core.py                     # Main AgentOrchestrator (LangGraph)
├── service.py                  # Service layer for CRUD
├── security.py                 # Prompt injection protection
├── exceptions.py               # Custom exceptions
├── models/
│   ├── __init__.py
│   ├── agent_model.py          # SQLAlchemy models
│   └── schemas.py              # Pydantic schemas
├── llm/
│   ├── __init__.py
│   ├── router.py               # Dynamic LLM Router
│   └── providers/
│       ├── __init__.py
│       ├── base.py             # Abstract base provider
│       ├── openai_provider.py
│       ├── ollama_provider.py
│       ├── gemini_provider.py
│       ├── claude_provider.py
│       └── huggingface_provider.py
├── tools/
│   ├── __init__.py
│   ├── base.py                 # Base tool class
│   ├── registry.py             # Tool registry
│   └── builtin/
│       ├── __init__.py
│       ├── github_tools.py
│       ├── slack_tools.py
│       ├── teams_tools.py
│       ├── telegram_tools.py
│       ├── web_tools.py
│       └── file_tools.py
└── memory/
    ├── __init__.py
    ├── manager.py              # Memory manager
    ├── conversation.py         # Short-term memory
    ├── vector.py               # Long-term vector memory
    └── session.py              # Session memory
```

## API Endpoints

### Agent CRUD

- `POST /api/v1/agents/` - Create agent
- `GET /api/v1/agents/` - List agents
- `GET /api/v1/agents/{id}` - Get agent
- `PATCH /api/v1/agents/{id}` - Update agent
- `DELETE /api/v1/agents/{id}` - Delete agent

### Agent Execution

- `POST /api/v1/agents/{id}/execute` - Execute agent (sync)
- `POST /api/v1/agents/{id}/stream` - Execute with streaming (SSE)

### History & Info

- `GET /api/v1/agents/{id}/conversations` - Get conversations
- `GET /api/v1/agents/{id}/executions` - Get execution history
- `GET /api/v1/agents/providers` - List LLM providers
- `GET /api/v1/agents/tools` - List available tools

## Configuration

Environment variables (in `.env`):

```env
# LLM Providers
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
GOOGLE_API_KEY=AIza...
HUGGINGFACE_API_KEY=hf_...

# Local LLM (Ollama)
ORCHESTRATOR_OLLAMA_BASE_URL=http://localhost:11434

# Connectors
GITHUB_TOKEN=ghp_...
SLACK_BOT_TOKEN=xoxb-...
TEAMS_WEBHOOK_URL=https://...
TELEGRAM_BOT_TOKEN=...

# Memory
ORCHESTRATOR_CHROMA_PERSIST_DIRECTORY=./data/chroma
```

## Usage Example

### Creating an Agent

```python
agent_data = {
    "name": "DevOps Assistant",
    "system_prompt": "You are a helpful DevOps assistant...",
    "goal": "Help users manage their infrastructure",
    "llm_provider": "openai",
    "model_name": "gpt-4o",
    "tools": [
        {"name": "github_list_issues"},
        {"name": "slack_send_message"},
    ],
    "permissions": {
        "can_access_internet": True,
        "can_send_messages": True,
    }
}
```

### Executing an Agent

```python
response = await orchestrator.run(
    agent_config=agent_config,
    message="Create an issue for the login bug",
    thread_id="conv-123"
)
print(response.response)
```

## Key Features

1. **LangGraph Execution**: Multi-step planning with tool use
2. **Security**: Prompt injection detection, permission validation
3. **Memory**: Conversation history, vector search, session data
4. **Streaming**: Real-time SSE responses
5. **Multi-Provider**: Switch LLMs dynamically per agent
6. **Tool Registry**: Extensible tool system with permissions

## Next Steps

1. Run database migrations for Agent models
2. Configure environment variables
3. Install dependencies: `pip install -r requirements.txt`
4. Test with: `uvicorn app.main:app --reload`
