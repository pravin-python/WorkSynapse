"""
Storage Infrastructure
======================
File storage abstraction supporting S3 and local filesystem.
"""

from app.infrastructure.storage.s3 import (
    StorageClient,
    storage_client,
)

__all__ = [
    "StorageClient",
    "storage_client",
]
