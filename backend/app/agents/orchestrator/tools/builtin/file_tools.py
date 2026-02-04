"""
File Tools
==========

Tools for file operations (read, write, list).
"""

import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Type

from app.agents.orchestrator.tools.base import BaseTool, ToolResult

logger = logging.getLogger(__name__)

# Safe directories that agents can access
SAFE_DIRECTORIES = [
    "./agent_workspace",
    "./data/agents",
    "/tmp/agents",
]


class FileReadTool(BaseTool):
    """Read content from a file."""

    name = "file_read"
    description = "Read content from a file within allowed directories"
    category = "file"
    required_permissions = ["can_access_files"]

    def get_parameters_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Path to the file to read",
                },
                "encoding": {
                    "type": "string",
                    "description": "File encoding (default: utf-8)",
                },
            },
            "required": ["path"],
        }

    async def execute(
        self,
        path: str,
        encoding: str = "utf-8",
        **kwargs,
    ) -> ToolResult:
        try:
            # Security check
            file_path = Path(path).resolve()
            is_safe = any(
                str(file_path).startswith(str(Path(d).resolve()))
                for d in SAFE_DIRECTORIES
            )

            if not is_safe:
                return ToolResult(
                    success=False,
                    error=f"Access denied: {path} is outside allowed directories",
                )

            if not file_path.exists():
                return ToolResult(
                    success=False,
                    error=f"File not found: {path}",
                )

            if not file_path.is_file():
                return ToolResult(
                    success=False,
                    error=f"Not a file: {path}",
                )

            # Read file
            content = file_path.read_text(encoding=encoding)

            return ToolResult(
                success=True,
                data={
                    "path": str(file_path),
                    "content": content,
                    "size": file_path.stat().st_size,
                },
            )

        except Exception as e:
            logger.error(f"File read error: {e}")
            return ToolResult(success=False, error=str(e))


class FileWriteTool(BaseTool):
    """Write content to a file."""

    name = "file_write"
    description = "Write content to a file within allowed directories"
    category = "file"
    required_permissions = ["can_access_files", "can_modify_data"]

    def get_parameters_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Path to the file to write",
                },
                "content": {
                    "type": "string",
                    "description": "Content to write to the file",
                },
                "mode": {
                    "type": "string",
                    "description": "Write mode: 'write' (overwrite) or 'append'",
                },
            },
            "required": ["path", "content"],
        }

    async def execute(
        self,
        path: str,
        content: str,
        mode: str = "write",
        **kwargs,
    ) -> ToolResult:
        try:
            # Security check
            file_path = Path(path).resolve()
            is_safe = any(
                str(file_path).startswith(str(Path(d).resolve()))
                for d in SAFE_DIRECTORIES
            )

            if not is_safe:
                return ToolResult(
                    success=False,
                    error=f"Access denied: {path} is outside allowed directories",
                )

            # Create parent directories if needed
            file_path.parent.mkdir(parents=True, exist_ok=True)

            # Write file
            write_mode = "a" if mode == "append" else "w"
            with open(file_path, write_mode, encoding="utf-8") as f:
                f.write(content)

            return ToolResult(
                success=True,
                data={
                    "path": str(file_path),
                    "size": file_path.stat().st_size,
                    "mode": mode,
                },
            )

        except Exception as e:
            logger.error(f"File write error: {e}")
            return ToolResult(success=False, error=str(e))


class FileListTool(BaseTool):
    """List files in a directory."""

    name = "file_list"
    description = "List files and directories within allowed paths"
    category = "file"
    required_permissions = ["can_access_files"]

    def get_parameters_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Directory path to list",
                },
                "pattern": {
                    "type": "string",
                    "description": "Glob pattern to filter files (e.g., '*.txt')",
                },
            },
            "required": ["path"],
        }

    async def execute(
        self,
        path: str,
        pattern: str = "*",
        **kwargs,
    ) -> ToolResult:
        try:
            # Security check
            dir_path = Path(path).resolve()
            is_safe = any(
                str(dir_path).startswith(str(Path(d).resolve()))
                for d in SAFE_DIRECTORIES
            )

            if not is_safe:
                return ToolResult(
                    success=False,
                    error=f"Access denied: {path} is outside allowed directories",
                )

            if not dir_path.exists():
                return ToolResult(
                    success=False,
                    error=f"Directory not found: {path}",
                )

            if not dir_path.is_dir():
                return ToolResult(
                    success=False,
                    error=f"Not a directory: {path}",
                )

            # List files
            files = []
            for item in dir_path.glob(pattern):
                files.append({
                    "name": item.name,
                    "path": str(item),
                    "is_dir": item.is_dir(),
                    "size": item.stat().st_size if item.is_file() else None,
                })

            return ToolResult(
                success=True,
                data={
                    "path": str(dir_path),
                    "files": files,
                    "count": len(files),
                },
            )

        except Exception as e:
            logger.error(f"File list error: {e}")
            return ToolResult(success=False, error=str(e))


class FileDeleteTool(BaseTool):
    """Delete a file."""

    name = "file_delete"
    description = "Delete a file within allowed directories"
    category = "file"
    required_permissions = ["can_access_files", "can_modify_data"]

    def get_parameters_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Path to the file to delete",
                },
            },
            "required": ["path"],
        }

    async def execute(
        self,
        path: str,
        **kwargs,
    ) -> ToolResult:
        try:
            # Security check
            file_path = Path(path).resolve()
            is_safe = any(
                str(file_path).startswith(str(Path(d).resolve()))
                for d in SAFE_DIRECTORIES
            )

            if not is_safe:
                return ToolResult(
                    success=False,
                    error=f"Access denied: {path} is outside allowed directories",
                )

            if not file_path.exists():
                return ToolResult(
                    success=False,
                    error=f"File not found: {path}",
                )

            if not file_path.is_file():
                return ToolResult(
                    success=False,
                    error=f"Not a file: {path}",
                )

            # Delete file
            file_path.unlink()

            return ToolResult(
                success=True,
                data={
                    "path": str(file_path),
                    "message": "File deleted successfully",
                },
            )

        except Exception as e:
            logger.error(f"File delete error: {e}")
            return ToolResult(success=False, error=str(e))


def get_tools() -> List[Type[BaseTool]]:
    """Return all file tool classes."""
    return [
        FileReadTool,
        FileWriteTool,
        FileListTool,
        FileDeleteTool,
    ]
