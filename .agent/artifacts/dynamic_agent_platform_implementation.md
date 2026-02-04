# 🤖 WorkSynapse Dynamic Agent Platform - Implementation Plan

## Overview

This document outlines the implementation of a **dynamic LangChain-based agent orchestration platform** for WorkSynapse. The platform enables:

- **Dynamic agent creation** from frontend/database configuration
- **Multi-LLM routing** (OpenAI, Ollama, HuggingFace, Gemini, Claude)
- **MCP tool integration** (GitHub, Slack, Teams, Telegram, etc.)
- **Memory systems** (conversation, vector, session-based)
- **LangGraph-powered planning** for multi-step reasoning

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                        FRONTEND (React/Next.js)                     │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐              │
│  │ Agent Creator │  │ Agent Manager│  │ Chat Interface│              │
│  └──────────────┘  └──────────────┘  └──────────────┘              │
└─────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      API LAYER (FastAPI)                            │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐              │
│  │  /agents     │  │  /chat       │  │  /tools      │              │
│  └──────────────┘  └──────────────┘  └──────────────┘              │
└─────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────┐
│                   AGENT ORCHESTRATOR SERVICE                        │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │                    OrchestratorCore                          │  │
│  │  ┌────────────┐  ┌────────────┐  ┌────────────┐             │  │
│  │  │ AgentLoader│  │ ToolLoader │  │ MemoryMgr  │             │  │
│  │  └────────────┘  └────────────┘  └────────────┘             │  │
│  │  ┌────────────┐  ┌────────────┐  ┌────────────┐             │  │
│  │  │ LLMRouter  │  │ GraphRunner│  │ SecurityMgr│             │  │
│  │  └────────────┘  └────────────┘  └────────────┘             │  │
│  └──────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
                                    │
          ┌─────────────────────────┼─────────────────────────┐
          │                         │                         │
          ▼                         ▼                         ▼
┌──────────────────┐   ┌──────────────────┐   ┌──────────────────┐
│   LLM PROVIDERS  │   │   MCP TOOLS      │   │   MEMORY STORES  │
│  ┌────────────┐  │   │  ┌────────────┐  │   │  ┌────────────┐  │
│  │  OpenAI    │  │   │  │  GitHub    │  │   │  │  Redis     │  │
│  │  Ollama    │  │   │  │  Slack     │  │   │  │  ChromaDB  │  │
│  │  Gemini    │  │   │  │  Teams     │  │   │  │  PostgreSQL│  │
│  │  Claude    │  │   │  │  Telegram  │  │   │  └────────────┘  │
│  │  HuggingFace│ │   │  │  HTTP APIs │  │   └──────────────────┘
│  └────────────┘  │   │  └────────────┘  │
└──────────────────┘   └──────────────────┘
```

---

## File Structure

```
backend/app/agents/orchestrator/
├── __init__.py
├── core.py                # Main orchestrator
├── config.py              # Orchestrator configuration
├── models/
│   ├── __init__.py
│   ├── agent_model.py     # SQLAlchemy Agent model
│   └── schemas.py         # Pydantic schemas
├── llm/
│   ├── __init__.py
│   ├── router.py          # LLM provider router
│   ├── providers/
│   │   ├── __init__.py
│   │   ├── base.py        # Base provider interface
│   │   ├── openai.py      # OpenAI provider
│   │   ├── ollama.py      # Ollama local provider
│   │   ├── gemini.py      # Google Gemini provider
│   │   ├── claude.py      # Anthropic Claude provider
│   │   └── huggingface.py # HuggingFace provider
├── tools/
│   ├── __init__.py
│   ├── registry.py        # Tool registration system
│   ├── loader.py          # Dynamic tool loader
│   ├── base.py            # Base tool interface
│   ├── mcp/
│   │   ├── __init__.py
│   │   ├── github.py      # GitHub MCP tools
│   │   ├── slack.py       # Slack connector
│   │   ├── teams.py       # Microsoft Teams connector
│   │   ├── telegram.py    # Telegram connector
│   │   └── http_api.py    # Generic HTTP API tool
│   └── builtin/
│       ├── __init__.py
│       ├── calculator.py  # Calculator tool
│       ├── web_search.py  # Web search tool
│       └── datetime.py    # Date/time utilities
├── memory/
│   ├── __init__.py
│   ├── manager.py         # Memory manager
│   ├── stores/
│   │   ├── __init__.py
│   │   ├── conversation.py # Conversation memory
│   │   ├── vector.py       # Vector memory (Chroma)
│   │   └── session.py      # Session-based memory
├── graph/
│   ├── __init__.py
│   ├── runner.py          # LangGraph execution
│   ├── nodes.py           # Graph nodes
│   └── state.py           # Agent state schema
├── security/
│   ├── __init__.py
│   ├── permissions.py     # Permission checking
│   ├── prompt_guard.py    # Prompt injection protection
│   └── rate_limiter.py    # Rate limiting
└── exceptions.py          # Custom exceptions
```

---

## Implementation Phases

### Phase 1: Core Infrastructure

1. Agent model and database schema
2. Base orchestrator structure
3. LLM router with OpenAI provider

### Phase 2: Multi-LLM Support

4. Additional LLM providers (Ollama, Gemini, Claude, HuggingFace)
2. Dynamic provider selection

### Phase 3: Tool System

6. Tool registry and loader
2. MCP tool implementations
3. Built-in utility tools

### Phase 4: Memory & State

9. Memory manager
2. Conversation and vector memory stores
3. LangGraph state management

### Phase 5: Execution Engine

12. LangGraph runner
2. Multi-step planning
3. Result handling

### Phase 6: API & Security

15. REST API endpoints
2. Security middleware
3. Rate limiting and permissions

---

## Database Schema

```sql
CREATE TABLE agents (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    system_prompt TEXT NOT NULL,
    goal TEXT,
    description TEXT,
    tools JSONB DEFAULT '[]',
    llm_provider VARCHAR(50) DEFAULT 'openai',
    model_name VARCHAR(100) DEFAULT 'gpt-4',
    memory_type VARCHAR(50) DEFAULT 'conversation',
    permissions JSONB DEFAULT '{}',
    config JSONB DEFAULT '{}',
    is_active BOOLEAN DEFAULT TRUE,
    created_by UUID REFERENCES users(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE agent_conversations (
    id SERIAL PRIMARY KEY,
    agent_id INTEGER REFERENCES agents(id),
    thread_id UUID NOT NULL,
    user_id UUID REFERENCES users(id),
    messages JSONB DEFAULT '[]',
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE agent_executions (
    id SERIAL PRIMARY KEY,
    agent_id INTEGER REFERENCES agents(id),
    conversation_id INTEGER REFERENCES agent_conversations(id),
    input_message TEXT NOT NULL,
    output_message TEXT,
    tool_calls JSONB DEFAULT '[]',
    tokens_used INTEGER DEFAULT 0,
    duration_ms INTEGER DEFAULT 0,
    status VARCHAR(50) DEFAULT 'pending',
    error TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

## Key Dependencies

```
langchain>=0.3.0
langchain-core>=0.3.0
langchain-openai>=0.2.0
langchain-anthropic>=0.2.0
langchain-google-genai>=2.0.0
langchain-community>=0.3.0
langgraph>=0.2.0
langgraph-checkpoint>=2.0.0
chromadb>=0.5.0
sentence-transformers>=3.0.0
httpx>=0.26.0
tiktoken>=0.7.0
```

---

## Success Criteria

- [ ] Agents can be created dynamically from API
- [ ] Multiple agents can run simultaneously
- [ ] Each agent supports custom system prompts and tools
- [ ] LLM provider can be switched per-agent
- [ ] Tools load dynamically based on agent config
- [ ] Memory is isolated per agent/conversation
- [ ] Security checks prevent prompt injection
- [ ] Rate limiting protects against abuse
