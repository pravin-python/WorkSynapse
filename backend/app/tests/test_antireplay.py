"""
Anti-Replay Security Tests
===========================
Unit tests for the anti-replay protection system.
"""
import pytest
import time
import uuid
import hmac
import hashlib
from unittest.mock import AsyncMock, MagicMock, patch

from fastapi import FastAPI
from fastapi.testclient import TestClient
from starlette.middleware.base import BaseHTTPMiddleware

# Import test targets
from app.middleware.antireplay import (
    SignatureService,
    TimestampService,
    NonceService,
    AntiReplayMiddleware,
    AntiReplayError,
    TIMESTAMP_TOLERANCE_SECONDS
)
from app.utils.antireplay_client import (
    AntiReplayClient,
    SyncAntiReplayClient,
    SignatureGenerator,
    generate_test_signature
)


class TestSignatureService:
    """Test HMAC signature generation and verification."""
    
    def test_compute_signature(self):
        """Test signature computation."""
        signature = SignatureService.compute_signature(
            method="POST",
            path="/api/v1/tasks",
            body='{"title":"Test"}',
            timestamp="1706979600",
            nonce="123e4567-e89b-12d3-a456-426614174000",
            secret_key="test-secret-key"
        )
        
        assert signature is not None
        assert len(signature) == 64  # SHA256 hex is 64 chars
        assert signature.islower()  # Should be lowercase hex
    
    def test_signature_consistency(self):
        """Test that same inputs produce same signature."""
        params = {
            "method": "GET",
            "path": "/api/v1/users",
            "body": "",
            "timestamp": "1706979600",
            "nonce": "123e4567-e89b-12d3-a456-426614174000",
            "secret_key": "my-secret"
        }
        
        sig1 = SignatureService.compute_signature(**params)
        sig2 = SignatureService.compute_signature(**params)
        
        assert sig1 == sig2
    
    def test_signature_differs_with_different_inputs(self):
        """Test that different inputs produce different signatures."""
        base_params = {
            "method": "POST",
            "path": "/api/v1/tasks",
            "body": '{"title":"Test"}',
            "timestamp": "1706979600",
            "nonce": "123e4567-e89b-12d3-a456-426614174000",
            "secret_key": "test-secret"
        }
        
        sig1 = SignatureService.compute_signature(**base_params)
        
        # Change method
        sig2 = SignatureService.compute_signature(
            **{**base_params, "method": "PUT"}
        )
        assert sig1 != sig2
        
        # Change path
        sig3 = SignatureService.compute_signature(
            **{**base_params, "path": "/api/v1/projects"}
        )
        assert sig1 != sig3
        
        # Change body
        sig4 = SignatureService.compute_signature(
            **{**base_params, "body": '{"title":"Different"}'}
        )
        assert sig1 != sig4
        
        # Change timestamp
        sig5 = SignatureService.compute_signature(
            **{**base_params, "timestamp": "1706979601"}
        )
        assert sig1 != sig5
        
        # Change nonce
        sig6 = SignatureService.compute_signature(
            **{**base_params, "nonce": str(uuid.uuid4())}
        )
        assert sig1 != sig6
    
    def test_verify_signature_valid(self):
        """Test signature verification with valid signature."""
        method = "POST"
        path = "/api/v1/tasks"
        body = '{"title":"Test"}'
        timestamp = "1706979600"
        nonce = str(uuid.uuid4())
        secret = "test-secret"
        
        # Generate signature
        signature = SignatureService.compute_signature(
            method, path, body, timestamp, nonce, secret
        )
        
        # Verify
        assert SignatureService.verify_signature(
            signature, method, path, body, timestamp, nonce, secret
        ) is True
    
    def test_verify_signature_invalid(self):
        """Test signature verification with invalid signature."""
        assert SignatureService.verify_signature(
            provided_signature="invalid-signature",
            method="POST",
            path="/api/v1/tasks",
            body="{}",
            timestamp="1706979600",
            nonce=str(uuid.uuid4()),
            secret_key="test-secret"
        ) is False
    
    def test_verify_signature_case_insensitive(self):
        """Test that signature verification is case-insensitive."""
        params = {
            "method": "POST",
            "path": "/api/v1/tasks",
            "body": "{}",
            "timestamp": "1706979600",
            "nonce": str(uuid.uuid4()),
            "secret_key": "test-secret"
        }
        
        signature = SignatureService.compute_signature(**params)
        
        # Verify with uppercase
        assert SignatureService.verify_signature(
            signature.upper(),
            params["method"],
            params["path"],
            params["body"],
            params["timestamp"],
            params["nonce"],
            params["secret_key"]
        ) is True


class TestTimestampService:
    """Test timestamp validation."""
    
    def test_valid_timestamp_current(self):
        """Test that current timestamp is valid."""
        timestamp = str(int(time.time()))
        is_valid, error = TimestampService.validate_timestamp(timestamp)
        
        assert is_valid is True
        assert error == ""
    
    def test_valid_timestamp_within_tolerance(self):
        """Test timestamp within tolerance window."""
        # 15 seconds in the past (within 30 second tolerance)
        timestamp = str(int(time.time()) - 15)
        is_valid, error = TimestampService.validate_timestamp(timestamp)
        
        assert is_valid is True
    
    def test_invalid_timestamp_too_old(self):
        """Test timestamp outside tolerance window (too old)."""
        # 60 seconds in the past (outside 30 second tolerance)
        timestamp = str(int(time.time()) - 60)
        is_valid, error = TimestampService.validate_timestamp(timestamp)
        
        assert is_valid is False
        assert "too large" in error
    
    def test_invalid_timestamp_too_future(self):
        """Test timestamp outside tolerance window (in future)."""
        # 60 seconds in the future
        timestamp = str(int(time.time()) + 60)
        is_valid, error = TimestampService.validate_timestamp(timestamp)
        
        assert is_valid is False
        assert "too large" in error
    
    def test_invalid_timestamp_format(self):
        """Test invalid timestamp format."""
        is_valid, error = TimestampService.validate_timestamp("not-a-number")
        
        assert is_valid is False
        assert "Invalid timestamp format" in error
    
    def test_invalid_timestamp_empty(self):
        """Test empty timestamp."""
        is_valid, error = TimestampService.validate_timestamp("")
        
        assert is_valid is False


class TestNonceService:
    """Test nonce validation."""
    
    def test_valid_uuid_format(self):
        """Test valid UUID v4 format."""
        valid_nonce = str(uuid.uuid4())
        assert NonceService.validate_nonce_format(valid_nonce) is True
    
    def test_valid_uuid_lowercase(self):
        """Test that lowercase UUID is valid."""
        nonce = str(uuid.uuid4()).lower()
        assert NonceService.validate_nonce_format(nonce) is True
    
    def test_invalid_uuid_format_random_string(self):
        """Test invalid UUID format (random string)."""
        assert NonceService.validate_nonce_format("not-a-uuid") is False
    
    def test_invalid_uuid_format_empty(self):
        """Test invalid UUID format (empty string)."""
        assert NonceService.validate_nonce_format("") is False
    
    def test_invalid_uuid_format_wrong_version(self):
        """Test that wrong UUID version might fail."""
        # UUID v1 format (time-based)
        uuid_v1 = str(uuid.uuid1())
        # Might still pass format check but version check could fail
        # depending on strict implementation


class TestAntiReplayClient:
    """Test client utility for generating secure requests."""
    
    def test_signature_generator(self):
        """Test signature generator creates valid headers."""
        generator = SignatureGenerator("test-secret")
        headers = generator.generate(
            method="POST",
            path="/api/v1/tasks",
            body='{"title":"Test"}'
        )
        
        assert headers.timestamp is not None
        assert headers.nonce is not None
        assert headers.signature is not None
        assert len(headers.signature) == 64
    
    def test_signature_generator_with_provided_values(self):
        """Test signature generator with provided timestamp and nonce."""
        generator = SignatureGenerator("test-secret")
        headers = generator.generate(
            method="GET",
            path="/api/v1/tasks",
            timestamp="1706979600",
            nonce="123e4567-e89b-12d3-a456-426614174000"
        )
        
        assert headers.timestamp == "1706979600"
        assert headers.nonce == "123e4567-e89b-12d3-a456-426614174000"
    
    def test_generate_headers_dict(self):
        """Test that headers convert to dictionary correctly."""
        generator = SignatureGenerator("test-secret")
        headers = generator.generate("GET", "/api/v1/tasks")
        headers.api_key = "my-api-key"
        
        header_dict = headers.to_dict()
        
        assert "X-API-KEY" in header_dict
        assert "X-TIMESTAMP" in header_dict
        assert "X-NONCE" in header_dict
        assert "X-SIGNATURE" in header_dict
        assert header_dict["X-API-KEY"] == "my-api-key"
    
    def test_sync_client_headers(self):
        """Test synchronous client generates correct headers."""
        client = SyncAntiReplayClient(
            api_key="test-api-key",
            secret_key="test-secret",
            base_url="http://localhost:8000"
        )
        
        headers = client.generate_headers("GET", "/api/v1/tasks")
        
        assert headers["X-API-KEY"] == "test-api-key"
        assert headers["X-TIMESTAMP"].isdigit()
        assert len(headers["X-NONCE"]) == 36  # UUID format
        assert len(headers["X-SIGNATURE"]) == 64
    
    def test_generate_test_signature(self):
        """Test the test signature generation utility."""
        headers = generate_test_signature(
            method="POST",
            path="/api/v1/tasks",
            body='{"title":"Test"}',
            secret_key="test-secret",
            api_key="my-api-key"
        )
        
        assert headers["X-API-KEY"] == "my-api-key"
        assert "X-TIMESTAMP" in headers
        assert "X-NONCE" in headers
        assert "X-SIGNATURE" in headers


class TestAntiReplayError:
    """Test error response generation."""
    
    def test_missing_headers_error(self):
        """Test missing headers error response."""
        response = AntiReplayError.missing_headers(["X-API-KEY", "X-NONCE"])
        
        assert response.status_code == 401
        content = response.body.decode()
        assert "missing_security_headers" in content
        assert "X-API-KEY" in content
        assert "X-NONCE" in content
    
    def test_invalid_api_key_error(self):
        """Test invalid API key error response."""
        response = AntiReplayError.invalid_api_key()
        
        assert response.status_code == 401
        content = response.body.decode()
        assert "invalid_api_key" in content
    
    def test_invalid_signature_error(self):
        """Test invalid signature error response."""
        response = AntiReplayError.invalid_signature()
        
        assert response.status_code == 403
        content = response.body.decode()
        assert "invalid_signature" in content
    
    def test_timestamp_expired_error(self):
        """Test timestamp expired error response."""
        response = AntiReplayError.timestamp_expired()
        
        assert response.status_code == 408
        content = response.body.decode()
        assert "timestamp_expired" in content
    
    def test_nonce_reused_error(self):
        """Test nonce reused error response."""
        response = AntiReplayError.nonce_reused()
        
        assert response.status_code == 409
        content = response.body.decode()
        assert "nonce_already_used" in content
    
    def test_rate_limited_error(self):
        """Test rate limited error response."""
        response = AntiReplayError.rate_limited(retry_after=60)
        
        assert response.status_code == 429
        assert response.headers.get("Retry-After") == "60"
        content = response.body.decode()
        assert "rate_limit_exceeded" in content
    
    def test_ip_blocked_error(self):
        """Test IP blocked error response."""
        response = AntiReplayError.ip_blocked()
        
        assert response.status_code == 403
        content = response.body.decode()
        assert "ip_blocked" in content


class TestIntegration:
    """Integration tests for the full middleware stack."""
    
    def test_signature_round_trip(self):
        """Test that client-generated signature passes server validation."""
        secret_key = "shared-secret-key"
        method = "POST"
        path = "/api/v1/tasks"
        body = '{"title":"Test Task","priority":"high"}'
        
        # Client side: generate signature
        client = SyncAntiReplayClient(
            api_key="test-api-key",
            secret_key=secret_key,
            base_url="http://localhost:8000"
        )
        headers = client.generate_headers(method, path, body)
        
        # Server side: verify signature
        is_valid = SignatureService.verify_signature(
            provided_signature=headers["X-SIGNATURE"],
            method=method,
            path=path,
            body=body,
            timestamp=headers["X-TIMESTAMP"],
            nonce=headers["X-NONCE"],
            secret_key=secret_key
        )
        
        assert is_valid is True
    
    def test_tampered_body_fails_verification(self):
        """Test that tampering with body causes signature failure."""
        secret_key = "shared-secret-key"
        method = "POST"
        path = "/api/v1/tasks"
        original_body = '{"title":"Test Task"}'
        tampered_body = '{"title":"Hacked Task"}'
        
        # Generate headers for original body
        headers = generate_test_signature(
            method=method,
            path=path,
            body=original_body,
            secret_key=secret_key
        )
        
        # Verify with tampered body
        is_valid = SignatureService.verify_signature(
            provided_signature=headers["X-SIGNATURE"],
            method=method,
            path=path,
            body=tampered_body,  # Tampered!
            timestamp=headers["X-TIMESTAMP"],
            nonce=headers["X-NONCE"],
            secret_key=secret_key
        )
        
        assert is_valid is False


# Run tests with: pytest tests/test_antireplay.py -v
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
