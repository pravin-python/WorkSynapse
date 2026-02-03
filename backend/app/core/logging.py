"""
Structured Logging Module with Security Event Tracking
"""
import logging
import json
import sys
from datetime import datetime
from typing import Any, Dict, Optional
from functools import wraps

class JSONFormatter(logging.Formatter):
    """JSON formatter for structured logging."""
    
    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        
        # Add extra fields if present
        if hasattr(record, "user_id"):
            log_data["user_id"] = record.user_id
        if hasattr(record, "request_id"):
            log_data["request_id"] = record.request_id
        if hasattr(record, "event_type"):
            log_data["event_type"] = record.event_type
        if hasattr(record, "ip_address"):
            log_data["ip_address"] = record.ip_address
            
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
            
        return json.dumps(log_data)

def setup_logging(log_level: str = "INFO") -> logging.Logger:
    """Setup structured JSON logging."""
    logger = logging.getLogger("worksynapse")
    logger.setLevel(getattr(logging, log_level.upper()))
    
    # Console handler with JSON formatting
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(JSONFormatter())
    logger.addHandler(console_handler)
    
    return logger

# Global logger instance
logger = setup_logging()

class SecurityLogger:
    """Specialized logger for security events."""
    
    @staticmethod
    def log_auth_success(user_id: str, ip_address: str):
        logger.info(
            "Authentication successful",
            extra={"user_id": user_id, "ip_address": ip_address, "event_type": "AUTH_SUCCESS"}
        )
    
    @staticmethod
    def log_auth_failure(email: str, ip_address: str, reason: str):
        logger.warning(
            f"Authentication failed: {reason}",
            extra={"email": email, "ip_address": ip_address, "event_type": "AUTH_FAILURE"}
        )
    
    @staticmethod
    def log_rate_limit(user_id: str, ip_address: str, endpoint: str):
        logger.warning(
            f"Rate limit exceeded for endpoint: {endpoint}",
            extra={"user_id": user_id, "ip_address": ip_address, "event_type": "RATE_LIMIT"}
        )
    
    @staticmethod
    def log_suspicious_activity(user_id: Optional[str], ip_address: str, details: str):
        logger.error(
            f"Suspicious activity detected: {details}",
            extra={"user_id": user_id, "ip_address": ip_address, "event_type": "SUSPICIOUS"}
        )
    
    @staticmethod
    def log_permission_denied(user_id: str, resource: str, action: str):
        logger.warning(
            f"Permission denied: {action} on {resource}",
            extra={"user_id": user_id, "event_type": "PERMISSION_DENIED"}
        )
    
    @staticmethod
    def log_replay_attack(ip_address: str, nonce: str, endpoint: str):
        """Log potential replay attack detection."""
        logger.error(
            f"Replay attack detected: nonce={nonce[:8]}... on {endpoint}",
            extra={"ip_address": ip_address, "event_type": "REPLAY_ATTACK", "nonce": nonce}
        )
    
    @staticmethod
    def log_signature_failure(ip_address: str, endpoint: str, reason: str = ""):
        """Log signature verification failure."""
        logger.warning(
            f"Signature verification failed for {endpoint}: {reason}",
            extra={"ip_address": ip_address, "event_type": "SIGNATURE_FAILURE"}
        )
    
    @staticmethod
    def log_timestamp_drift(ip_address: str, drift_seconds: int, endpoint: str):
        """Log excessive timestamp drift."""
        logger.warning(
            f"Timestamp drift {drift_seconds}s detected for {endpoint}",
            extra={"ip_address": ip_address, "event_type": "TIMESTAMP_DRIFT", "drift": drift_seconds}
        )
    
    @staticmethod
    def log_ip_blocked(ip_address: str, reason: str):
        """Log IP blocking event."""
        logger.warning(
            f"IP blocked: {ip_address} - {reason}",
            extra={"ip_address": ip_address, "event_type": "IP_BLOCKED"}
        )
    
    @staticmethod
    def log_antireplay_success(ip_address: str, endpoint: str, method: str):
        """Log successful anti-replay validation."""
        logger.debug(
            f"Anti-replay validation passed for {method} {endpoint}",
            extra={"ip_address": ip_address, "event_type": "ANTIREPLAY_SUCCESS"}
        )

class AuditLogger:
    """Logger for audit trail events."""
    
    @staticmethod
    def log_create(user_id: str, resource_type: str, resource_id: str):
        logger.info(
            f"Created {resource_type}:{resource_id}",
            extra={"user_id": user_id, "event_type": "AUDIT_CREATE"}
        )
    
    @staticmethod
    def log_update(user_id: str, resource_type: str, resource_id: str, changes: Dict[str, Any]):
        logger.info(
            f"Updated {resource_type}:{resource_id}",
            extra={"user_id": user_id, "event_type": "AUDIT_UPDATE", "changes": str(changes)}
        )
    
    @staticmethod
    def log_delete(user_id: str, resource_type: str, resource_id: str):
        logger.info(
            f"Deleted {resource_type}:{resource_id}",
            extra={"user_id": user_id, "event_type": "AUDIT_DELETE"}
        )

security_logger = SecurityLogger()
audit_logger = AuditLogger()
