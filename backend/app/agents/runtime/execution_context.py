"""
Execution Context
=================

Context object for agent execution.
"""

from typing import Optional, Dict, Any
from pydantic import BaseModel, Field

class ExecutionContext(BaseModel):
    """
    Context for a single agent execution request.
    """
    agent_id: int
    user_id: str
    thread_id: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
