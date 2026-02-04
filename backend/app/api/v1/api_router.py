from fastapi import APIRouter
from app.api.v1.routers import users, auth, projects, tasks, chat, agents, webhooks, notes, worklogs, files, llm_keys, user_activity
from app.api.v1.endpoints import websockets

api_router = APIRouter()

# Auth routes
api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])

# User routes
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(user_activity.router, prefix="/user/activity", tags=["user-activity"])

# Project routes
api_router.include_router(projects.router, prefix="/projects", tags=["projects"])

# Task routes
api_router.include_router(tasks.router, prefix="/tasks", tags=["tasks"])

# Chat routes
api_router.include_router(chat.router, prefix="/chat", tags=["chat"])

# Notes routes
api_router.include_router(notes.router, prefix="/notes", tags=["notes"])

# Agents routes
api_router.include_router(agents.router, prefix="/agents", tags=["agents"])

# Worklogs routes
api_router.include_router(worklogs.router, prefix="/worklogs", tags=["worklogs"])

# Files routes
api_router.include_router(files.router, prefix="/files", tags=["files"])

# Webhooks routes
api_router.include_router(webhooks.router, prefix="/webhooks", tags=["webhooks"])

# WebSocket routes
api_router.include_router(websockets.router, tags=["websockets"])

# LLM Keys routes (API key management for AI providers)
api_router.include_router(llm_keys.router, prefix="/llm", tags=["llm-keys"])

