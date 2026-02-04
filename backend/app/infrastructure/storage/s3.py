"""
S3-Compatible Storage Client
============================
File storage abstraction supporting S3 and local filesystem.

Features:
- S3 and MinIO compatible
- Fallback to local filesystem
- Presigned URL generation
- File upload/download
"""

import os
from typing import Optional, BinaryIO
from io import BytesIO
import mimetypes

from app.core.config import settings
from app.core.logging import logger


class StorageClient:
    """
    Storage client abstraction.
    
    Supports S3, MinIO, and local filesystem storage.
    """
    
    def __init__(self):
        self._s3_client = None
        self._bucket_name = getattr(settings, 'S3_BUCKET_NAME', 'worksynapse')
        self._use_local = getattr(settings, 'USE_LOCAL_STORAGE', True)
        self._local_path = getattr(settings, 'LOCAL_STORAGE_PATH', './uploads')
    
    async def initialize(self):
        """Initialize the storage client."""
        if self._use_local:
            # Ensure local directory exists
            os.makedirs(self._local_path, exist_ok=True)
            logger.info(f"Using local storage at: {self._local_path}")
        else:
            try:
                import boto3
                self._s3_client = boto3.client(
                    's3',
                    endpoint_url=getattr(settings, 'S3_ENDPOINT_URL', None),
                    aws_access_key_id=getattr(settings, 'AWS_ACCESS_KEY_ID', None),
                    aws_secret_access_key=getattr(settings, 'AWS_SECRET_ACCESS_KEY', None),
                    region_name=getattr(settings, 'AWS_REGION', 'us-east-1'),
                )
                logger.info("S3 storage client initialized")
            except ImportError:
                logger.warning("boto3 not installed, falling back to local storage")
                self._use_local = True
                os.makedirs(self._local_path, exist_ok=True)
    
    async def upload_file(
        self,
        file: BinaryIO,
        key: str,
        content_type: Optional[str] = None
    ) -> str:
        """
        Upload a file to storage.
        
        Args:
            file: File-like object to upload
            key: Storage key/path
            content_type: MIME type of the file
            
        Returns:
            URL or path to the uploaded file
        """
        if content_type is None:
            content_type = mimetypes.guess_type(key)[0] or 'application/octet-stream'
        
        if self._use_local:
            # Local storage
            file_path = os.path.join(self._local_path, key)
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
            with open(file_path, 'wb') as f:
                if hasattr(file, 'read'):
                    f.write(file.read())
                else:
                    f.write(file)
            
            return f"/uploads/{key}"
        else:
            # S3 storage
            self._s3_client.upload_fileobj(
                file,
                self._bucket_name,
                key,
                ExtraArgs={'ContentType': content_type}
            )
            return f"s3://{self._bucket_name}/{key}"
    
    async def download_file(self, key: str) -> Optional[bytes]:
        """
        Download a file from storage.
        
        Args:
            key: Storage key/path
            
        Returns:
            File contents as bytes, or None if not found
        """
        if self._use_local:
            file_path = os.path.join(self._local_path, key)
            if os.path.exists(file_path):
                with open(file_path, 'rb') as f:
                    return f.read()
            return None
        else:
            try:
                response = self._s3_client.get_object(
                    Bucket=self._bucket_name,
                    Key=key
                )
                return response['Body'].read()
            except Exception:
                return None
    
    async def delete_file(self, key: str) -> bool:
        """
        Delete a file from storage.
        
        Args:
            key: Storage key/path
            
        Returns:
            True if deleted, False otherwise
        """
        if self._use_local:
            file_path = os.path.join(self._local_path, key)
            if os.path.exists(file_path):
                os.remove(file_path)
                return True
            return False
        else:
            try:
                self._s3_client.delete_object(
                    Bucket=self._bucket_name,
                    Key=key
                )
                return True
            except Exception:
                return False
    
    async def get_presigned_url(
        self,
        key: str,
        expires_in: int = 3600
    ) -> Optional[str]:
        """
        Generate a presigned URL for file access.
        
        Args:
            key: Storage key/path
            expires_in: URL expiration in seconds
            
        Returns:
            Presigned URL string
        """
        if self._use_local:
            # For local storage, return the local path
            return f"/uploads/{key}"
        else:
            try:
                url = self._s3_client.generate_presigned_url(
                    'get_object',
                    Params={
                        'Bucket': self._bucket_name,
                        'Key': key
                    },
                    ExpiresIn=expires_in
                )
                return url
            except Exception:
                return None
    
    async def file_exists(self, key: str) -> bool:
        """Check if a file exists in storage."""
        if self._use_local:
            file_path = os.path.join(self._local_path, key)
            return os.path.exists(file_path)
        else:
            try:
                self._s3_client.head_object(
                    Bucket=self._bucket_name,
                    Key=key
                )
                return True
            except Exception:
                return False


# Singleton instance
storage_client = StorageClient()
