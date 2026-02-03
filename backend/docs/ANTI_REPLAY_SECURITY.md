# 🔐 Anti-Replay API Security System

## Overview

WorkSynapse implements a **Zepto-style anti-replay protection system** that ensures every API request can only be used once. This prevents:

- ✅ **Replay attacks** - Captured requests cannot be re-sent
- ✅ **Duplicate submissions** - Same request blocked if sent twice
- ✅ **Request tampering** - Modified requests are detected
- ✅ **Man-in-the-middle attacks** - Captured requests expire quickly

## 🏗️ Architecture

```
┌─────────────────┐     ┌──────────────────────────────────────┐
│   API Client    │────▶│          FastAPI Backend             │
│                 │     │                                      │
│ ┌─────────────┐ │     │  ┌──────────────────────────────┐   │
│ │ Generate:   │ │     │  │    Anti-Replay Middleware    │   │
│ │ - Nonce     │ │     │  │                              │   │
│ │ - Timestamp │ │     │  │  1. Validate Headers         │   │
│ │ - Signature │ │     │  │  2. Check API Key            │   │
│ └─────────────┘ │     │  │  3. Verify Timestamp         │   │
│                 │     │  │  4. Check Nonce (Redis)      │   │
│                 │     │  │  5. Verify Signature         │   │
│                 │     │  │  6. Mark Nonce Used          │   │
│                 │     │  └──────────────────────────────┘   │
│                 │     │                 │                    │
│                 │     │                 ▼                    │
│                 │     │  ┌──────────────────────────────┐   │
│                 │     │  │         Redis                │   │
│                 │     │  │  - Nonce Store (60s TTL)     │   │
│                 │     │  │  - Rate Limiting             │   │
│                 │     │  │  - IP Throttling             │   │
│                 │     │  │  - Blocked IPs               │   │
│                 │     │  └──────────────────────────────┘   │
└─────────────────┘     └──────────────────────────────────────┘
```

## 📋 Required Headers

Every protected API request must include these headers:

| Header | Description | Example |
|--------|-------------|---------|
| `X-API-KEY` | Client API key for authentication | `sk_live_abc123...` |
| `X-TIMESTAMP` | Unix timestamp (seconds) | `1706979600` |
| `X-NONCE` | UUID v4, unique per request | `123e4567-e89b-12d3-a456-426614174000` |
| `X-SIGNATURE` | HMAC-SHA256 signature | `a1b2c3d4e5f6...` |

## 🔒 Signature Generation

The signature is computed using HMAC-SHA256:

```
signature = HMAC_SHA256(
    method + url_path + request_body + timestamp + nonce,
    SECRET_KEY
)
```

### Python Example

```python
import hmac
import hashlib
import time
import uuid

def generate_signature(method, path, body, timestamp, nonce, secret_key):
    message = f"{method.upper()}{path}{body}{timestamp}{nonce}"
    return hmac.new(
        secret_key.encode('utf-8'),
        message.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()

# Generate headers for a request
timestamp = str(int(time.time()))
nonce = str(uuid.uuid4())
body = '{"title":"New Task"}'

signature = generate_signature(
    method="POST",
    path="/api/v1/tasks",
    body=body,
    timestamp=timestamp,
    nonce=nonce,
    secret_key="your-secret-key"
)

headers = {
    "X-API-KEY": "your-api-key",
    "X-TIMESTAMP": timestamp,
    "X-NONCE": nonce,
    "X-SIGNATURE": signature,
    "Content-Type": "application/json"
}
```

### JavaScript Example

```javascript
async function generateSignature(method, path, body, timestamp, nonce, secretKey) {
    const encoder = new TextEncoder();
    const message = `${method.toUpperCase()}${path}${body}${timestamp}${nonce}`;
    
    const key = await crypto.subtle.importKey(
        'raw',
        encoder.encode(secretKey),
        { name: 'HMAC', hash: 'SHA-256' },
        false,
        ['sign']
    );
    
    const signature = await crypto.subtle.sign(
        'HMAC',
        key,
        encoder.encode(message)
    );
    
    return Array.from(new Uint8Array(signature))
        .map(b => b.toString(16).padStart(2, '0'))
        .join('');
}

// Usage
const timestamp = Math.floor(Date.now() / 1000).toString();
const nonce = crypto.randomUUID();
const body = JSON.stringify({ title: 'New Task' });

const signature = await generateSignature(
    'POST',
    '/api/v1/tasks',
    body,
    timestamp,
    nonce,
    'your-secret-key'
);
```

## 🛠️ Using the Python Client

WorkSynapse provides a ready-to-use client utility:

```python
from app.utils.antireplay_client import AntiReplayClient, SyncAntiReplayClient

# Async client
async def example_async():
    client = AntiReplayClient(
        api_key="your-api-key",
        secret_key="your-secret-key",
        base_url="http://localhost:8000"
    )
    
    # GET request
    response = await client.get("/api/v1/tasks")
    
    # POST request
    response = await client.post(
        "/api/v1/tasks",
        json_data={"title": "New Task", "priority": "high"}
    )

# Sync client
def example_sync():
    client = SyncAntiReplayClient(
        api_key="your-api-key",
        secret_key="your-secret-key",
        base_url="http://localhost:8000"
    )
    
    response = client.get("/api/v1/tasks")
    print(response.json())
```

## ❌ Error Responses

The anti-replay system returns structured errors:

### 401 - Missing Headers
```json
{
    "error": "missing_security_headers",
    "message": "Required security headers missing: X-API-KEY, X-NONCE",
    "code": "SECURITY_401",
    "timestamp": "2024-02-04T12:00:00Z"
}
```

### 401 - Invalid API Key
```json
{
    "error": "invalid_api_key",
    "message": "The provided API key is invalid or not recognized",
    "code": "SECURITY_401_KEY",
    "timestamp": "2024-02-04T12:00:00Z"
}
```

### 403 - Invalid Signature
```json
{
    "error": "invalid_signature",
    "message": "Request signature verification failed. Request may have been tampered.",
    "code": "SECURITY_403",
    "timestamp": "2024-02-04T12:00:00Z"
}
```

### 408 - Timestamp Expired
```json
{
    "error": "timestamp_expired",
    "message": "Request timestamp is outside the acceptable window (±30 seconds)",
    "code": "SECURITY_408",
    "timestamp": "2024-02-04T12:00:00Z"
}
```

### 409 - Nonce Already Used
```json
{
    "error": "nonce_already_used",
    "message": "This request has already been processed. Replay attack detected.",
    "code": "SECURITY_409",
    "timestamp": "2024-02-04T12:00:00Z"
}
```

### 429 - Rate Limited
```json
{
    "error": "rate_limit_exceeded",
    "message": "Too many requests. Please slow down.",
    "code": "SECURITY_429",
    "retry_after": 60,
    "timestamp": "2024-02-04T12:00:00Z"
}
```

## ⚙️ Configuration

Environment variables for anti-replay security:

```bash
# Enable/disable anti-replay protection
ANTIREPLAY_ENABLED=true

# Timestamp tolerance in seconds (±30 seconds)
ANTIREPLAY_TIMESTAMP_TOLERANCE=30

# Nonce TTL in seconds
ANTIREPLAY_NONCE_TTL=60

# Rate limits
ANTIREPLAY_IP_RATE_LIMIT=100
ANTIREPLAY_API_KEY_RATE_LIMIT=200

# Suspicious activity thresholds
ANTIREPLAY_SUSPICIOUS_THRESHOLD=5
ANTIREPLAY_BLOCK_DURATION=900
```

## 🚫 Exempt Endpoints

The following endpoints do NOT require anti-replay headers:

- `/health` - Health check
- `/metrics` - Prometheus metrics
- `/` - Root endpoint
- `/api/v1/auth/login` - Login
- `/api/v1/auth/register` - Registration
- `/api/v1/auth/refresh` - Token refresh
- `/api/v1/docs` - API documentation
- `/api/v1/openapi.json` - OpenAPI spec
- `/api/v1/redoc` - ReDoc documentation

Webhooks have their own verification:
- `/api/v1/webhooks/github`
- `/api/v1/webhooks/jira`

## 🧪 Testing

### Using cURL

```bash
# Generate headers manually
TIMESTAMP=$(date +%s)
NONCE=$(uuidgen)
BODY='{"title":"Test"}'
SECRET="your-secret-key"
API_KEY="your-api-key"
PATH="/api/v1/tasks"
METHOD="POST"

# Compute signature (using openssl)
MESSAGE="${METHOD}${PATH}${BODY}${TIMESTAMP}${NONCE}"
SIGNATURE=$(echo -n "$MESSAGE" | openssl dgst -sha256 -hmac "$SECRET" | awk '{print $2}')

# Make request
curl -X POST "http://localhost:8000${PATH}" \
  -H "Content-Type: application/json" \
  -H "X-API-KEY: ${API_KEY}" \
  -H "X-TIMESTAMP: ${TIMESTAMP}" \
  -H "X-NONCE: ${NONCE}" \
  -H "X-SIGNATURE: ${SIGNATURE}" \
  -d "$BODY"
```

### Using the Test Utility

```python
from app.utils.antireplay_client import generate_test_signature

headers = generate_test_signature(
    method="GET",
    path="/api/v1/tasks",
    body="",
    secret_key="your-secret-key",
    api_key="your-api-key"
)

print("Use these headers for testing:")
for k, v in headers.items():
    print(f"  {k}: {v}")
```

### Disable for Local Development

Set in your `.env`:

```bash
ANTIREPLAY_ENABLED=false
```

## 🔍 Security Logging

All security events are logged:

- `ANTIREPLAY_SUCCESS` - Successful validation
- `REPLAY_ATTACK` - Nonce reuse detected
- `SIGNATURE_FAILURE` - Invalid signature
- `TIMESTAMP_DRIFT` - Expired timestamp
- `IP_BLOCKED` - IP temporarily blocked
- `RATE_LIMIT` - Rate limit exceeded

Example log entry:
```json
{
    "timestamp": "2024-02-04T12:00:00.000Z",
    "level": "WARNING",
    "event_type": "REPLAY_ATTACK",
    "ip_address": "192.168.1.100",
    "nonce": "123e4567-e89b-12d3-a456-426614174000",
    "message": "Replay attack detected"
}
```

## 📊 Redis Key Structure

| Key Pattern | Purpose | TTL |
|-------------|---------|-----|
| `antireplay:nonce:{nonce}` | Used nonces | 60s |
| `antireplay:ip:{ip}` | IP request count | 60s |
| `antireplay:apikey:{hash}` | API key request count | 60s |
| `antireplay:suspicious:{ip}:count` | Suspicious activity count | 15m |
| `antireplay:suspicious:{ip}` | IP block flag | 15m |

## 🏛️ Best Practices

1. **Generate new nonce for every request** - Never reuse nonces
2. **Sync time with NTP** - Keep client/server time synchronized
3. **Store API keys securely** - Never expose in frontend code
4. **Use HTTPS** - Encrypt all traffic
5. **Monitor logs** - Watch for suspicious patterns
6. **Rate limit appropriately** - Adjust based on traffic

## 🔧 Troubleshooting

### "Timestamp expired" errors
- Check client system time
- Ensure NTP synchronization
- Increase `ANTIREPLAY_TIMESTAMP_TOLERANCE` if needed

### "Nonce already used" errors
- Ensure unique nonce for each request
- Use UUID v4 generator
- Don't retry failed requests with same nonce

### "Invalid signature" errors
- Verify secret key matches on client/server
- Check request body is exactly the same
- Ensure proper URL encoding
- Verify HTTP method is uppercase in signature

### Redis connection issues
- Check Redis is running
- Verify `REDIS_URL` configuration
- Check network connectivity
