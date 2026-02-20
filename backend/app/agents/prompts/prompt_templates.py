"""
Prompt Templates
================

Templates and storage for dynamic prompts.
"""

from typing import Dict, List, Optional
from app.agents.prompts.prompt_types import PromptType, PromptPart

class PromptTemplate:
    """
    Template for a prompt.
    """
    def __init__(self, name: str, parts: List[PromptPart]):
        self.name = name
        self.parts = parts

class PromptTemplateStore:
    """
    Store for prompt templates. In a real app, this would be a DB.
    """
    _templates: Dict[str, PromptTemplate] = {}

    @classmethod
    def get_template(cls, name: str) -> Optional[PromptTemplate]:
        return cls._templates.get(name)

    @classmethod
    def save_template(cls, template: PromptTemplate):
        cls._templates[template.name] = template

# Default parts
DEFAULT_SYSTEM_PART = PromptPart(type=PromptType.SYSTEM, content="You are a helpful AI assistant.")
DEFAULT_GOAL_PART = PromptPart(type=PromptType.GOAL, content="Help the user with their request.")
DEFAULT_INSTRUCTION_PART = PromptPart(type=PromptType.INSTRUCTION, content="Answer concisely and accurately.")
