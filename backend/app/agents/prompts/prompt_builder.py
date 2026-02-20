"""
Prompt Builder
==============

Builds dynamic prompts for agents.
"""

import logging
from typing import List, Optional, Dict, Any
from langchain_core.messages import BaseMessage, SystemMessage, HumanMessage, AIMessage

from app.agents.prompts.prompt_types import PromptType, PromptPart
from app.agents.prompts.prompt_templates import PromptTemplateStore, DEFAULT_SYSTEM_PART
from app.agents.rag.retriever import get_retriever

logger = logging.getLogger(__name__)

class PromptBuilder:
    """
    Builds dynamic prompts for agents.
    """

    def __init__(self, agent_config: Dict[str, Any]):
        self.config = agent_config
        self.retriever = get_retriever()

    async def build_messages(
        self,
        user_message: str,
        conversation_history: List[BaseMessage] = None,
        context: Optional[str] = None
    ) -> List[BaseMessage]:
        """
        Build the full message list for the LLM.
        """
        parts: List[PromptPart] = []

        # 1. Fetch from DB/Template
        template_name = self.config.get("prompt_template_name")
        template = PromptTemplateStore.get_template(template_name) if template_name else None

        if template:
            parts.extend(template.parts)
        else:
            # Fallback/Default Construction
            if self.config.get("system_prompt"):
                parts.append(PromptPart(type=PromptType.SYSTEM, content=self.config["system_prompt"]))
            else:
                 parts.append(DEFAULT_SYSTEM_PART)

            if self.config.get("goal"):
                 parts.append(PromptPart(type=PromptType.GOAL, content=self.config["goal"]))

            if self.config.get("instruction"):
                 parts.append(PromptPart(type=PromptType.INSTRUCTION, content=self.config["instruction"]))

            # Tools (optional description in prompt)
            # Typically handled by bind_tools, but can be added here if needed for older models
            # We skip explicit tool descriptions here assuming native tool calling or bind_tools usage

        # 2. RAG Context (if enabled)
        if self.config.get("rag_enabled", False):
            # If context not provided, retrieve it
            if not context and user_message:
                try:
                    docs = await self.retriever.retrieve(user_message, k=5)
                    if docs:
                        context = "\n---\n".join(docs)
                except Exception as e:
                    logger.error(f"Failed to retrieve context: {e}")

            if context:
                parts.append(PromptPart(type=PromptType.CONTEXT, content=f"Relevant Context:\n{context}"))

        # 3. Assemble System Prompt
        system_content_parts = []
        for p in parts:
            if p.type in [PromptType.SYSTEM, PromptType.GOAL, PromptType.INSTRUCTION, PromptType.CONTEXT, PromptType.TOOL, PromptType.OUTPUT]:
                 # Uppercase prefix for clarity
                 prefix = p.type.name.upper()
                 if p.content:
                    system_content_parts.append(f"{prefix}:\n{p.content}")

        full_system_prompt = "\n\n".join(system_content_parts)

        messages = [SystemMessage(content=full_system_prompt)]

        # 4. Add Conversation History
        if conversation_history:
            messages.extend(conversation_history)

        # 5. Add User Message
        if user_message:
            messages.append(HumanMessage(content=user_message))

        return messages
