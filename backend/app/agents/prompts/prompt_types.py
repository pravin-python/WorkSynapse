"""
Prompt Types
============

Enumerations and types for the dynamic prompt system.
"""

from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

class PromptType(str, Enum):
    """
    Types of prompt components.
    """
    SYSTEM = "system"
    GOAL = "goal"
    INSTRUCTION = "instruction"
    CONTEXT = "context"
    TOOL = "tool"
    MEMORY = "memory"
    SCRATCHPAD = "scratchpad"
    OUTPUT = "output"

class PromptPart(BaseModel):
    """
    A single part of a prompt.
    """
    type: PromptType
    content: str
    metadata: Dict[str, Any] = Field(default_factory=dict)
