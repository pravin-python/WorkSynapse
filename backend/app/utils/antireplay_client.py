"""
Anti-Replay Client Utility
===========================
Client-side utility for generating secure API requests with HMAC signatures.

This utility can be used by:
- Python clients/scripts
- Service-to-service communication
- Testing and development

Usage:
    from app.utils.antireplay_client import AntiReplayClient
    
    client = AntiReplayClient(
        api_key="your-api-key",
        secret_key="your-secret-key",
        base_url="http://localhost:8000"
    )
    
    # Make a GET request
    response = await client.get("/api/v1/tasks")
    
    # Make a POST request
    response = await client.post("/api/v1/tasks", json={"title": "New Task"})
"""
import time
import uuid
import hmac
import hashlib
import json
from typing import Optional, Dict, Any, Union
from dataclasses import dataclass


@dataclass
class SecurityHeaders:
    """Security headers for anti-replay protection."""
    api_key: str
    timestamp: str
    nonce: str
    signature: str
    
    def to_dict(self) -> Dict[str, str]:
        """Convert to dictionary for use in HTTP headers."""
        return {
            "X-API-KEY": self.api_key,
            "X-TIMESTAMP": self.timestamp,
            "X-NONCE": self.nonce,
            "X-SIGNATURE": self.signature
        }


class SignatureGenerator:
    """
    Generate HMAC-SHA256 signatures for API requests.
    
    The signature is computed as:
    HMAC_SHA256(method + path + body + timestamp + nonce, secret_key)
    """
    
    def __init__(self, secret_key: str):
        self.secret_key = secret_key
    
    def generate(
        self,
        method: str,
        path: str,
        body: str = "",
        timestamp: Optional[str] = None,
        nonce: Optional[str] = None
    ) -> SecurityHeaders:
        """
        Generate security headers for a request.
        
        Args:
            method: HTTP method (GET, POST, etc.)
            path: URL path (e.g., /api/v1/tasks)
            body: Request body as JSON string (empty for GET)
            timestamp: Unix timestamp (auto-generated if not provided)
            nonce: UUID v4 nonce (auto-generated if not provided)
            
        Returns:
            SecurityHeaders object with all required headers
        """
        if timestamp is None:
            timestamp = str(int(time.time()))
        
        if nonce is None:
            nonce = str(uuid.uuid4())
        
        # Construct message
        message = f"{method.upper()}{path}{body}{timestamp}{nonce}"
        
        # Compute HMAC-SHA256
        signature = hmac.new(
            self.secret_key.encode('utf-8'),
            message.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        return SecurityHeaders(
            api_key="",  # Set by client
            timestamp=timestamp,
            nonce=nonce,
            signature=signature
        )


class AntiReplayClient:
    """
    HTTP client with automatic anti-replay header generation.
    
    Wraps httpx or aiohttp to automatically add security headers to requests.
    """
    
    def __init__(
        self,
        api_key: str,
        secret_key: str,
        base_url: str = "http://localhost:8000"
    ):
        """
        Initialize the anti-replay client.
        
        Args:
            api_key: Your API key for authentication
            secret_key: Secret key for HMAC signature generation
            base_url: Base URL of the API server
        """
        self.api_key = api_key
        self.secret_key = secret_key
        self.base_url = base_url.rstrip('/')
        self.signature_generator = SignatureGenerator(secret_key)
    
    def generate_headers(
        self,
        method: str,
        path: str,
        body: str = ""
    ) -> Dict[str, str]:
        """
        Generate security headers for a request.
        
        Args:
            method: HTTP method
            path: URL path
            body: Request body as string
            
        Returns:
            Dictionary of headers to include in request
        """
        headers = self.signature_generator.generate(
            method=method,
            path=path,
            body=body
        )
        headers.api_key = self.api_key
        return headers.to_dict()
    
    async def request(
        self,
        method: str,
        path: str,
        json_data: Optional[Dict[str, Any]] = None,
        data: Optional[str] = None,
        headers: Optional[Dict[str, str]] = None,
        **kwargs
    ):
        """
        Make an HTTP request with anti-replay headers.
        
        Args:
            method: HTTP method
            path: URL path (will be appended to base_url)
            json_data: JSON payload (will be serialized)
            data: Raw string payload
            headers: Additional headers
            **kwargs: Additional arguments passed to httpx
            
        Returns:
            httpx.Response object
        """
        import httpx
        
        # Prepare body
        if json_data is not None:
            body = json.dumps(json_data, separators=(',', ':'))
        elif data is not None:
            body = data
        else:
            body = ""
        
        # Generate security headers
        security_headers = self.generate_headers(method, path, body)
        
        # Merge with additional headers
        all_headers = {**(headers or {}), **security_headers}
        
        # Add content type for JSON
        if json_data is not None:
            all_headers["Content-Type"] = "application/json"
        
        url = f"{self.base_url}{path}"
        
        async with httpx.AsyncClient() as client:
            if json_data is not None:
                response = await client.request(
                    method,
                    url,
                    content=body,
                    headers=all_headers,
                    **kwargs
                )
            elif data is not None:
                response = await client.request(
                    method,
                    url,
                    content=data,
                    headers=all_headers,
                    **kwargs
                )
            else:
                response = await client.request(
                    method,
                    url,
                    headers=all_headers,
                    **kwargs
                )
        
        return response
    
    async def get(self, path: str, **kwargs):
        """Make a GET request."""
        return await self.request("GET", path, **kwargs)
    
    async def post(
        self,
        path: str,
        json_data: Optional[Dict[str, Any]] = None,
        **kwargs
    ):
        """Make a POST request."""
        return await self.request("POST", path, json_data=json_data, **kwargs)
    
    async def put(
        self,
        path: str,
        json_data: Optional[Dict[str, Any]] = None,
        **kwargs
    ):
        """Make a PUT request."""
        return await self.request("PUT", path, json_data=json_data, **kwargs)
    
    async def patch(
        self,
        path: str,
        json_data: Optional[Dict[str, Any]] = None,
        **kwargs
    ):
        """Make a PATCH request."""
        return await self.request("PATCH", path, json_data=json_data, **kwargs)
    
    async def delete(self, path: str, **kwargs):
        """Make a DELETE request."""
        return await self.request("DELETE", path, **kwargs)


class SyncAntiReplayClient:
    """
    Synchronous version of AntiReplayClient for non-async contexts.
    """
    
    def __init__(
        self,
        api_key: str,
        secret_key: str,
        base_url: str = "http://localhost:8000"
    ):
        self.api_key = api_key
        self.secret_key = secret_key
        self.base_url = base_url.rstrip('/')
        self.signature_generator = SignatureGenerator(secret_key)
    
    def generate_headers(
        self,
        method: str,
        path: str,
        body: str = ""
    ) -> Dict[str, str]:
        """Generate security headers for a request."""
        headers = self.signature_generator.generate(
            method=method,
            path=path,
            body=body
        )
        headers.api_key = self.api_key
        return headers.to_dict()
    
    def request(
        self,
        method: str,
        path: str,
        json_data: Optional[Dict[str, Any]] = None,
        data: Optional[str] = None,
        headers: Optional[Dict[str, str]] = None,
        **kwargs
    ):
        """Make an HTTP request with anti-replay headers."""
        import httpx
        
        # Prepare body
        if json_data is not None:
            body = json.dumps(json_data, separators=(',', ':'))
        elif data is not None:
            body = data
        else:
            body = ""
        
        # Generate security headers
        security_headers = self.generate_headers(method, path, body)
        
        # Merge with additional headers
        all_headers = {**(headers or {}), **security_headers}
        
        # Add content type for JSON
        if json_data is not None:
            all_headers["Content-Type"] = "application/json"
        
        url = f"{self.base_url}{path}"
        
        with httpx.Client() as client:
            if json_data is not None:
                response = client.request(
                    method,
                    url,
                    content=body,
                    headers=all_headers,
                    **kwargs
                )
            elif data is not None:
                response = client.request(
                    method,
                    url,
                    content=data,
                    headers=all_headers,
                    **kwargs
                )
            else:
                response = client.request(
                    method,
                    url,
                    headers=all_headers,
                    **kwargs
                )
        
        return response
    
    def get(self, path: str, **kwargs):
        """Make a GET request."""
        return self.request("GET", path, **kwargs)
    
    def post(
        self,
        path: str,
        json_data: Optional[Dict[str, Any]] = None,
        **kwargs
    ):
        """Make a POST request."""
        return self.request("POST", path, json_data=json_data, **kwargs)
    
    def put(
        self,
        path: str,
        json_data: Optional[Dict[str, Any]] = None,
        **kwargs
    ):
        """Make a PUT request."""
        return self.request("PUT", path, json_data=json_data, **kwargs)
    
    def patch(
        self,
        path: str,
        json_data: Optional[Dict[str, Any]] = None,
        **kwargs
    ):
        """Make a PATCH request."""
        return self.request("PATCH", path, json_data=json_data, **kwargs)
    
    def delete(self, path: str, **kwargs):
        """Make a DELETE request."""
        return self.request("DELETE", path, **kwargs)


# ============================================================================
# JAVASCRIPT IMPLEMENTATION (for frontend)
# ============================================================================

JAVASCRIPT_CLIENT = '''
/**
 * Anti-Replay Client for JavaScript/TypeScript
 * 
 * Usage:
 *   import { createSecureRequest } from './antireplay';
 *   
 *   const headers = await createSecureRequest({
 *     method: 'POST',
 *     path: '/api/v1/tasks',
 *     body: JSON.stringify({ title: 'New Task' }),
 *     apiKey: 'your-api-key',
 *     secretKey: 'your-secret-key'
 *   });
 *   
 *   fetch('http://localhost:8000/api/v1/tasks', {
 *     method: 'POST',
 *     headers: {
 *       'Content-Type': 'application/json',
 *       ...headers
 *     },
 *     body: JSON.stringify({ title: 'New Task' })
 *   });
 */

async function generateHMAC(message, secretKey) {
  const encoder = new TextEncoder();
  const keyData = encoder.encode(secretKey);
  const messageData = encoder.encode(message);
  
  const key = await crypto.subtle.importKey(
    'raw',
    keyData,
    { name: 'HMAC', hash: 'SHA-256' },
    false,
    ['sign']
  );
  
  const signature = await crypto.subtle.sign('HMAC', key, messageData);
  return Array.from(new Uint8Array(signature))
    .map(b => b.toString(16).padStart(2, '0'))
    .join('');
}

function generateUUID() {
  return crypto.randomUUID();
}

export async function createSecureRequest({
  method,
  path,
  body = '',
  apiKey,
  secretKey
}) {
  const timestamp = Math.floor(Date.now() / 1000).toString();
  const nonce = generateUUID();
  
  const message = `${method.toUpperCase()}${path}${body}${timestamp}${nonce}`;
  const signature = await generateHMAC(message, secretKey);
  
  return {
    'X-API-KEY': apiKey,
    'X-TIMESTAMP': timestamp,
    'X-NONCE': nonce,
    'X-SIGNATURE': signature
  };
}

export class AntiReplayClient {
  constructor(apiKey, secretKey, baseUrl = 'http://localhost:8000') {
    this.apiKey = apiKey;
    this.secretKey = secretKey;
    this.baseUrl = baseUrl.replace(/\/$/, '');
  }
  
  async request(method, path, options = {}) {
    const body = options.body ? JSON.stringify(options.body) : '';
    
    const securityHeaders = await createSecureRequest({
      method,
      path,
      body,
      apiKey: this.apiKey,
      secretKey: this.secretKey
    });
    
    const response = await fetch(`${this.baseUrl}${path}`, {
      method,
      headers: {
        'Content-Type': 'application/json',
        ...securityHeaders,
        ...options.headers
      },
      body: body || undefined
    });
    
    return response;
  }
  
  get(path, options) {
    return this.request('GET', path, options);
  }
  
  post(path, body, options) {
    return this.request('POST', path, { ...options, body });
  }
  
  put(path, body, options) {
    return this.request('PUT', path, { ...options, body });
  }
  
  patch(path, body, options) {
    return this.request('PATCH', path, { ...options, body });
  }
  
  delete(path, options) {
    return this.request('DELETE', path, options);
  }
}
'''


def get_javascript_client() -> str:
    """Return JavaScript client implementation."""
    return JAVASCRIPT_CLIENT


# ============================================================================
# TESTING UTILITIES
# ============================================================================

def generate_test_signature(
    method: str,
    path: str,
    body: str,
    secret_key: str,
    timestamp: Optional[str] = None,
    nonce: Optional[str] = None,
    api_key: str = "test-api-key"
) -> Dict[str, str]:
    """
    Generate test security headers for manual testing.
    
    Returns:
        Dictionary of headers to use in test requests
    """
    timestamp = timestamp or str(int(time.time()))
    nonce = nonce or str(uuid.uuid4())
    
    message = f"{method.upper()}{path}{body}{timestamp}{nonce}"
    signature = hmac.new(
        secret_key.encode('utf-8'),
        message.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()
    
    return {
        "X-API-KEY": api_key,
        "X-TIMESTAMP": timestamp,
        "X-NONCE": nonce,
        "X-SIGNATURE": signature
    }


if __name__ == "__main__":
    # Example usage
    import asyncio
    
    async def demo():
        client = AntiReplayClient(
            api_key="your-api-key",
            secret_key="your-secret-key",
            base_url="http://localhost:8000"
        )
        
        # Generate headers for curl testing
        headers = client.generate_headers("GET", "/api/v1/tasks")
        print("Generated headers for GET /api/v1/tasks:")
        for k, v in headers.items():
            print(f"  {k}: {v}")
        
        # Generate headers for POST request
        body = '{"title":"Test Task"}'
        headers = client.generate_headers("POST", "/api/v1/tasks", body)
        print("\nGenerated headers for POST /api/v1/tasks:")
        for k, v in headers.items():
            print(f"  {k}: {v}")
    
    asyncio.run(demo())
