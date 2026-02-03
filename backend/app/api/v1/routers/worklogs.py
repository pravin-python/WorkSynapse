"""Worklogs Router"""
from fastapi import APIRouter, Depends
from app.api.deps import get_current_user
from app.models.user.model import User

router = APIRouter()

@router.get("/")
async def list_worklogs(current_user: User = Depends(get_current_user)):
    return []

@router.post("/start")
async def start_worklog(current_user: User = Depends(get_current_user)):
    return {"status": "started"}

@router.post("/stop")
async def stop_worklog(current_user: User = Depends(get_current_user)):
    return {"status": "stopped"}
