"""
GitHub Tools
============

Tools for interacting with GitHub repositories.
"""

import logging
from typing import Any, Dict, List, Optional, Type
import httpx

from app.agents.tools.base import BaseTool, ToolResult
from app.agents.orchestrator.config import get_orchestrator_config

logger = logging.getLogger(__name__)


class GitHubSearchRepositoriesTool(BaseTool):
    """Search for GitHub repositories."""

    name = "github_search_repos"
    description = "Search for GitHub repositories by query"
    category = "github"
    required_permissions = ["can_access_internet", "can_access_github"]

    def get_parameters_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Search query for repositories",
                },
                "per_page": {
                    "type": "integer",
                    "description": "Number of results per page (max 100)",
                },
            },
            "required": ["query"],
        }

    async def execute(
        self,
        query: str,
        per_page: int = 10,
        **kwargs,
    ) -> ToolResult:
        try:
            config = get_orchestrator_config()
            headers = {"Accept": "application/vnd.github+json"}
            if config.github_token:
                headers["Authorization"] = f"Bearer {config.github_token}"

            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{config.github_api_url}/search/repositories",
                    params={"q": query, "per_page": min(per_page, 100)},
                    headers=headers,
                    timeout=30,
                )
                response.raise_for_status()
                data = response.json()

            repos = [
                {
                    "name": repo["full_name"],
                    "description": repo["description"],
                    "stars": repo["stargazers_count"],
                    "url": repo["html_url"],
                }
                for repo in data.get("items", [])
            ]

            return ToolResult(success=True, data=repos)

        except Exception as e:
            logger.error(f"GitHub search error: {e}")
            return ToolResult(success=False, error=str(e))


class GitHubGetRepositoryTool(BaseTool):
    """Get information about a GitHub repository."""

    name = "github_get_repo"
    description = "Get details about a specific GitHub repository"
    category = "github"
    required_permissions = ["can_access_internet", "can_access_github"]

    def get_parameters_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "owner": {
                    "type": "string",
                    "description": "Repository owner (username or organization)",
                },
                "repo": {
                    "type": "string",
                    "description": "Repository name",
                },
            },
            "required": ["owner", "repo"],
        }

    async def execute(
        self,
        owner: str,
        repo: str,
        **kwargs,
    ) -> ToolResult:
        try:
            config = get_orchestrator_config()
            headers = {"Accept": "application/vnd.github+json"}
            if config.github_token:
                headers["Authorization"] = f"Bearer {config.github_token}"

            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{config.github_api_url}/repos/{owner}/{repo}",
                    headers=headers,
                    timeout=30,
                )
                response.raise_for_status()
                data = response.json()

            return ToolResult(
                success=True,
                data={
                    "name": data["full_name"],
                    "description": data["description"],
                    "stars": data["stargazers_count"],
                    "forks": data["forks_count"],
                    "language": data["language"],
                    "url": data["html_url"],
                    "default_branch": data["default_branch"],
                },
            )

        except Exception as e:
            logger.error(f"GitHub get repo error: {e}")
            return ToolResult(success=False, error=str(e))


class GitHubListIssuesTool(BaseTool):
    """List issues in a GitHub repository."""

    name = "github_list_issues"
    description = "List issues in a GitHub repository"
    category = "github"
    required_permissions = ["can_access_internet", "can_access_github"]

    def get_parameters_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "owner": {
                    "type": "string",
                    "description": "Repository owner",
                },
                "repo": {
                    "type": "string",
                    "description": "Repository name",
                },
                "state": {
                    "type": "string",
                    "description": "Issue state: open, closed, or all",
                },
                "per_page": {
                    "type": "integer",
                    "description": "Number of results per page",
                },
            },
            "required": ["owner", "repo"],
        }

    async def execute(
        self,
        owner: str,
        repo: str,
        state: str = "open",
        per_page: int = 10,
        **kwargs,
    ) -> ToolResult:
        try:
            config = get_orchestrator_config()
            headers = {"Accept": "application/vnd.github+json"}
            if config.github_token:
                headers["Authorization"] = f"Bearer {config.github_token}"

            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{config.github_api_url}/repos/{owner}/{repo}/issues",
                    params={"state": state, "per_page": min(per_page, 100)},
                    headers=headers,
                    timeout=30,
                )
                response.raise_for_status()
                data = response.json()

            issues = [
                {
                    "number": issue["number"],
                    "title": issue["title"],
                    "state": issue["state"],
                    "url": issue["html_url"],
                    "created_at": issue["created_at"],
                }
                for issue in data
            ]

            return ToolResult(success=True, data=issues)

        except Exception as e:
            logger.error(f"GitHub list issues error: {e}")
            return ToolResult(success=False, error=str(e))


class GitHubCreateIssueTool(BaseTool):
    """Create an issue in a GitHub repository."""

    name = "github_create_issue"
    description = "Create a new issue in a GitHub repository"
    category = "github"
    required_permissions = ["can_access_internet", "can_access_github", "can_modify_data"]

    def get_parameters_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "owner": {
                    "type": "string",
                    "description": "Repository owner",
                },
                "repo": {
                    "type": "string",
                    "description": "Repository name",
                },
                "title": {
                    "type": "string",
                    "description": "Issue title",
                },
                "body": {
                    "type": "string",
                    "description": "Issue body/description",
                },
            },
            "required": ["owner", "repo", "title"],
        }

    async def execute(
        self,
        owner: str,
        repo: str,
        title: str,
        body: str = "",
        **kwargs,
    ) -> ToolResult:
        try:
            config = get_orchestrator_config()
            if not config.github_token:
                return ToolResult(
                    success=False,
                    error="GitHub token not configured",
                )

            headers = {
                "Accept": "application/vnd.github+json",
                "Authorization": f"Bearer {config.github_token}",
            }

            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{config.github_api_url}/repos/{owner}/{repo}/issues",
                    json={"title": title, "body": body},
                    headers=headers,
                    timeout=30,
                )
                response.raise_for_status()
                data = response.json()

            return ToolResult(
                success=True,
                data={
                    "number": data["number"],
                    "url": data["html_url"],
                    "title": data["title"],
                },
            )

        except Exception as e:
            logger.error(f"GitHub create issue error: {e}")
            return ToolResult(success=False, error=str(e))


class GitHubGetFileContentsTool(BaseTool):
    """Get file contents from a GitHub repository."""

    name = "github_get_file"
    description = "Get the contents of a file from a GitHub repository"
    category = "github"
    required_permissions = ["can_access_internet", "can_access_github"]

    def get_parameters_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "owner": {
                    "type": "string",
                    "description": "Repository owner",
                },
                "repo": {
                    "type": "string",
                    "description": "Repository name",
                },
                "path": {
                    "type": "string",
                    "description": "Path to the file",
                },
                "branch": {
                    "type": "string",
                    "description": "Branch name (optional)",
                },
            },
            "required": ["owner", "repo", "path"],
        }

    async def execute(
        self,
        owner: str,
        repo: str,
        path: str,
        branch: Optional[str] = None,
        **kwargs,
    ) -> ToolResult:
        try:
            config = get_orchestrator_config()
            headers = {"Accept": "application/vnd.github+json"}
            if config.github_token:
                headers["Authorization"] = f"Bearer {config.github_token}"

            params = {}
            if branch:
                params["ref"] = branch

            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{config.github_api_url}/repos/{owner}/{repo}/contents/{path}",
                    params=params,
                    headers=headers,
                    timeout=30,
                )
                response.raise_for_status()
                data = response.json()

            # Decode base64 content
            import base64

            content = ""
            if data.get("encoding") == "base64" and data.get("content"):
                content = base64.b64decode(data["content"]).decode("utf-8")

            return ToolResult(
                success=True,
                data={
                    "path": data["path"],
                    "name": data["name"],
                    "content": content,
                    "size": data["size"],
                    "url": data["html_url"],
                },
            )

        except Exception as e:
            logger.error(f"GitHub get file error: {e}")
            return ToolResult(success=False, error=str(e))


def get_tools() -> List[Type[BaseTool]]:
    """Return all GitHub tool classes."""
    return [
        GitHubSearchRepositoriesTool,
        GitHubGetRepositoryTool,
        GitHubListIssuesTool,
        GitHubCreateIssueTool,
        GitHubGetFileContentsTool,
    ]
