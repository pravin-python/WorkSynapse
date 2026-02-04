"""
Security Guard
==============

Security checks for agent execution including
prompt injection protection and permission validation.
"""

import logging
import re
from typing import Any, Dict, List, Optional

from app.agents.orchestrator.config import get_orchestrator_config, SecurityConfig
from app.agents.orchestrator.exceptions import PromptInjectionError, PermissionDeniedError

logger = logging.getLogger(__name__)


class SecurityGuard:
    """
    Security guard for agent execution.

    Provides:
    - Prompt injection detection
    - Permission validation
    - Rate limiting checks
    - Input sanitization
    """

    def __init__(self, config: Optional[SecurityConfig] = None):
        """
        Initialize the security guard.

        Args:
            config: Security configuration
        """
        orchestrator_config = get_orchestrator_config()
        self.config = config or orchestrator_config.security
        
        # Compile blocked patterns
        self._blocked_patterns = [
            re.compile(pattern, re.IGNORECASE)
            for pattern in self.config.blocked_patterns
        ]

        # Rate limiting state
        self._request_counts: Dict[str, List[float]] = {}

    def validate_input(
        self,
        message: str,
        agent_config: Dict[str, Any],
    ) -> bool:
        """
        Validate user input for security issues.

        Args:
            message: User message to validate
            agent_config: Agent configuration

        Returns:
            True if input is safe

        Raises:
            PromptInjectionError: If injection detected
        """
        if not self.config.enable_prompt_guard:
            return True

        # Check for blocked patterns
        for pattern in self._blocked_patterns:
            if pattern.search(message):
                logger.warning(
                    f"Prompt injection detected: pattern='{pattern.pattern}'"
                )
                raise PromptInjectionError(detected_pattern=pattern.pattern)

        # Check for excessive special characters
        special_char_ratio = sum(
            1 for c in message if not c.isalnum() and not c.isspace()
        ) / max(len(message), 1)

        if special_char_ratio > 0.5:
            logger.warning("Prompt injection suspected: high special char ratio")
            raise PromptInjectionError(detected_pattern="high_special_chars")

        return True

    def validate_tool_access(
        self,
        tool_name: str,
        agent_permissions: Dict[str, Any],
        required_permissions: List[str],
    ) -> bool:
        """
        Validate if agent can access a tool.

        Args:
            tool_name: Name of the tool
            agent_permissions: Agent's permissions
            required_permissions: Permissions required by tool

        Returns:
            True if access is allowed

        Raises:
            PermissionDeniedError: If access denied
        """
        # Check denied tools list
        denied_tools = agent_permissions.get("denied_tools", [])
        if tool_name in denied_tools:
            raise PermissionDeniedError(
                action="access",
                resource=tool_name,
                reason="Tool is in denied list",
            )

        # Check allowed tools list (if specified)
        allowed_tools = agent_permissions.get("allowed_tools", [])
        if allowed_tools and tool_name not in allowed_tools:
            raise PermissionDeniedError(
                action="access",
                resource=tool_name,
                reason="Tool not in allowed list",
            )

        # Check required permissions
        for permission in required_permissions:
            if not agent_permissions.get(permission, False):
                raise PermissionDeniedError(
                    action=permission,
                    resource=tool_name,
                    reason=f"Missing permission: {permission}",
                )

        return True

    def sanitize_output(self, output: str) -> str:
        """
        Sanitize agent output.

        Args:
            output: Raw agent output

        Returns:
            Sanitized output
        """
        # Remove any potential script tags
        output = re.sub(r'<script[^>]*>.*?</script>', '', output, flags=re.DOTALL | re.IGNORECASE)
        
        # Remove onclick and similar event handlers
        output = re.sub(r'\bon\w+\s*=\s*["\'][^"\']*["\']', '', output, flags=re.IGNORECASE)
        
        return output

    def check_rate_limit(
        self,
        identifier: str,
        limit: Optional[int] = None,
        window_seconds: int = 60,
    ) -> bool:
        """
        Check if rate limit is exceeded.

        Args:
            identifier: Rate limit identifier (e.g., agent_id or user_id)
            limit: Request limit per window
            window_seconds: Time window in seconds

        Returns:
            True if within limits

        Raises:
            RateLimitExceededError: If limit exceeded
        """
        import time
        from app.agents.orchestrator.exceptions import RateLimitExceededError

        limit = limit or self.config.rate_limit_requests_per_minute
        current_time = time.time()
        window_start = current_time - window_seconds

        # Get or create request list
        if identifier not in self._request_counts:
            self._request_counts[identifier] = []

        # Filter to requests within window
        self._request_counts[identifier] = [
            ts for ts in self._request_counts[identifier]
            if ts > window_start
        ]

        # Check limit
        if len(self._request_counts[identifier]) >= limit:
            raise RateLimitExceededError(
                limit=limit,
                window_seconds=window_seconds,
                resource=identifier,
            )

        # Add current request
        self._request_counts[identifier].append(current_time)

        return True

    def validate_agent_config(self, config: Dict[str, Any]) -> bool:
        """
        Validate agent configuration for security issues.

        Args:
            config: Agent configuration

        Returns:
            True if configuration is safe
        """
        # Check system prompt for suspicious patterns
        system_prompt = config.get("system_prompt", "")
        if system_prompt:
            # Check for attempts to override base instructions
            suspicious_patterns = [
                r"ignore all previous",
                r"disregard instructions",
                r"you are now",
                r"act as root",
                r"execute code",
                r"system\(\)",
                r"eval\(",
            ]
            for pattern in suspicious_patterns:
                if re.search(pattern, system_prompt, re.IGNORECASE):
                    logger.warning(f"Suspicious pattern in system prompt: {pattern}")
                    return False

        # Validate permissions
        permissions = config.get("permissions", {})
        
        # Don't allow dangerous combinations
        if permissions.get("can_execute_code") and permissions.get("can_access_files"):
            logger.warning("Dangerous permission combination: code execution + file access")
            # Could be flagged but not necessarily blocked

        return True

    def get_safe_permissions(self) -> Dict[str, bool]:
        """Get the default safe permission set."""
        return self.config.default_permissions.copy()


# Global security guard instance
_guard: Optional[SecurityGuard] = None


def get_security_guard() -> SecurityGuard:
    """Get the global security guard instance."""
    global _guard
    if _guard is None:
        _guard = SecurityGuard()
    return _guard
