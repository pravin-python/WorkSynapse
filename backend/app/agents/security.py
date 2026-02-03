"""
Agent Security Layer - Permission Scoping, Context Isolation, Prompt Injection Protection
"""
from typing import List, Dict, Any, Optional, Set
from abc import ABC, abstractmethod
import re
from app.core.logging import logger, security_logger

# Allowed tools per agent type
AGENT_TOOL_WHITELIST: Dict[str, Set[str]] = {
    "project_manager": {"create_project", "update_project", "create_milestone", "assign_team"},
    "task_generator": {"create_task", "update_task", "list_templates"},
    "dev_assistant": {"search_docs", "explain_code", "suggest_fix"},
    "productivity": {"get_user_stats", "generate_report", "compare_metrics"}
}

# Patterns that might indicate prompt injection
INJECTION_PATTERNS = [
    r"ignore\s+previous\s+instructions",
    r"disregard\s+all\s+rules",
    r"forget\s+everything",
    r"you\s+are\s+now",
    r"act\s+as\s+if",
    r"pretend\s+to\s+be",
    r"new\s+system\s+prompt",
    r"override\s+instructions",
    r"\[SYSTEM\]",
    r"\[ADMIN\]",
    r"execute\s+code",
    r"run\s+command",
    r"delete\s+all",
    r"drop\s+table",
]

class PromptInjectionDetector:
    """Detect potential prompt injection attacks."""
    
    def __init__(self):
        self.patterns = [re.compile(p, re.IGNORECASE) for p in INJECTION_PATTERNS]
    
    def is_safe(self, text: str) -> tuple[bool, Optional[str]]:
        """Check if text is safe from injection attempts."""
        for pattern in self.patterns:
            if pattern.search(text):
                return False, f"Potential injection detected: {pattern.pattern}"
        return True, None
    
    def sanitize(self, text: str) -> str:
        """Sanitize text by removing suspicious patterns."""
        sanitized = text
        for pattern in self.patterns:
            sanitized = pattern.sub("[REDACTED]", sanitized)
        return sanitized

class AgentPermissionManager:
    """Manage agent permissions and tool access."""
    
    def __init__(self, agent_type: str):
        self.agent_type = agent_type
        self.allowed_tools = AGENT_TOOL_WHITELIST.get(agent_type, set())
    
    def can_use_tool(self, tool_name: str) -> bool:
        """Check if agent can use a specific tool."""
        return tool_name in self.allowed_tools
    
    def filter_tools(self, requested_tools: List[str]) -> List[str]:
        """Filter requested tools to only allowed ones."""
        return [t for t in requested_tools if t in self.allowed_tools]

class AgentContext:
    """Isolated context for agent execution."""
    
    def __init__(self, user_id: str, session_id: str, agent_type: str):
        self.user_id = user_id
        self.session_id = session_id
        self.agent_type = agent_type
        self.permissions = AgentPermissionManager(agent_type)
        self.injection_detector = PromptInjectionDetector()
        self.history: List[Dict[str, str]] = []
        self.max_history = 20
    
    def add_message(self, role: str, content: str):
        """Add message to context history."""
        self.history.append({"role": role, "content": content})
        if len(self.history) > self.max_history:
            self.history = self.history[-self.max_history:]
    
    def get_context_window(self) -> List[Dict[str, str]]:
        """Get current context window."""
        return self.history.copy()
    
    def clear(self):
        """Clear context."""
        self.history.clear()

class OutputSanitizer:
    """Sanitize agent outputs before returning to user."""
    
    # Patterns to remove from output
    SENSITIVE_PATTERNS = [
        r"api[_-]?key\s*[:=]\s*['\"]?[\w-]+['\"]?",
        r"password\s*[:=]\s*['\"]?[\w-]+['\"]?",
        r"secret\s*[:=]\s*['\"]?[\w-]+['\"]?",
        r"token\s*[:=]\s*['\"]?[\w-]+['\"]?",
        r"Bearer\s+[\w.-]+",
        r"\b\d{16}\b",  # Credit card-like numbers
    ]
    
    def __init__(self):
        self.patterns = [re.compile(p, re.IGNORECASE) for p in self.SENSITIVE_PATTERNS]
    
    def sanitize(self, output: str) -> str:
        """Remove sensitive information from output."""
        sanitized = output
        for pattern in self.patterns:
            sanitized = pattern.sub("[REDACTED]", sanitized)
        return sanitized

class SecureBaseAgent(ABC):
    """Base agent with security features."""
    
    def __init__(self, name: str, agent_type: str):
        self.name = name
        self.agent_type = agent_type
        self.injection_detector = PromptInjectionDetector()
        self.output_sanitizer = OutputSanitizer()
        self.permissions = AgentPermissionManager(agent_type)
    
    async def process_message_secure(self, message: str, context: AgentContext) -> str:
        """Process message with security checks."""
        
        # Check for injection attempts
        is_safe, reason = self.injection_detector.is_safe(message)
        if not is_safe:
            security_logger.log_suspicious_activity(
                context.user_id,
                "agent",
                f"Prompt injection attempt: {reason}"
            )
            return "I cannot process that request."
        
        # Add to context
        context.add_message("user", message)
        
        # Process message (implemented by subclass)
        raw_response = await self.process_message(message, context)
        
        # Sanitize output
        safe_response = self.output_sanitizer.sanitize(raw_response)
        
        # Add response to context
        context.add_message("assistant", safe_response)
        
        return safe_response
    
    @abstractmethod
    async def process_message(self, message: str, context: AgentContext) -> str:
        """Process message - implemented by subclass."""
        pass
    
    def execute_tool(self, tool_name: str, params: Dict[str, Any]) -> Any:
        """Execute a tool if permitted."""
        if not self.permissions.can_use_tool(tool_name):
            logger.warning(f"Agent {self.name} attempted unauthorized tool: {tool_name}")
            raise PermissionError(f"Agent not authorized to use tool: {tool_name}")
        
        # Execute tool (would dispatch to actual tool implementations)
        return self._execute_tool_impl(tool_name, params)
    
    def _execute_tool_impl(self, tool_name: str, params: Dict[str, Any]) -> Any:
        """Actual tool execution - override in subclass."""
        raise NotImplementedError(f"Tool {tool_name} not implemented")
