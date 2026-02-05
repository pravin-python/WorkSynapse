"""
Project Domain
==============
Project-related models, schemas, and services.

Re-exports from the models layer for backward compatibility.
"""

from app.models.project.model import (
    Project,
    ProjectStatus,
    Priority,
)

__all__ = [
    "Project",
    "ProjectStatus",
    "Priority",
]
