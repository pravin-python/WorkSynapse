"""
WorkSynapse Audit Logging Module
================================
Security audit trail and activity logging.

Features:
- Activity logging
- Security event logging
- Audit trail maintenance
"""
from typing import Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
import logging

logger = logging.getLogger(__name__)
security_logger = logging.getLogger("security")


class AuditLogger:
    """
    Log all significant actions for audit trail.
    
    Usage:
        await AuditLogger.log_activity(
            db,
            user_id=user.id,
            activity_type=ActivityType.CREATE,
            resource_type="project",
            resource_id=project.id,
            action="created",
            description="Created new project"
        )
    """
    
    @staticmethod
    async def log_activity(
        db: AsyncSession,
        *,
        user_id: Optional[int],
        activity_type,  # ActivityType enum
        resource_type: str,
        resource_id: Optional[int] = None,
        resource_name: Optional[str] = None,
        action: str,
        description: Optional[str] = None,
        old_values: Optional[dict] = None,
        new_values: Optional[dict] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        request_method: Optional[str] = None,
        request_path: Optional[str] = None,
    ):
        """
        Log an activity to the audit trail.
        
        Args:
            db: Database session
            user_id: ID of user performing action
            activity_type: Type of activity
            resource_type: Type of resource affected
            resource_id: ID of resource affected
            resource_name: Name of resource affected
            action: Action description
            description: Detailed description
            old_values: Previous values (for updates)
            new_values: New values (for updates)
            ip_address: Client IP
            user_agent: Client user agent
            request_method: HTTP method
            request_path: Request path
        """
        from app.models.worklog.model import ActivityLog
        
        activity = ActivityLog(
            user_id=user_id,
            activity_type=activity_type,
            resource_type=resource_type,
            resource_id=resource_id,
            resource_name=resource_name,
            action=action,
            description=description,
            old_values=old_values,
            new_values=new_values,
            ip_address=ip_address,
            user_agent=user_agent,
            request_method=request_method,
            request_path=request_path,
        )
        
        db.add(activity)
        await db.commit()
        
        logger.info(
            f"Activity logged: {activity_type.value} - {action}",
            extra={
                "user_id": user_id,
                "resource_type": resource_type,
                "resource_id": resource_id,
            }
        )
    
    @staticmethod
    async def log_security_event(
        db: AsyncSession,
        *,
        event_type: str,
        severity: str,
        user_id: Optional[int] = None,
        email_attempted: Optional[str] = None,
        ip_address: str,
        user_agent: Optional[str] = None,
        description: str,
        details: Optional[dict] = None,
        action_taken: Optional[str] = None,
    ):
        """
        Log a security event.
        
        Args:
            db: Database session
            event_type: Type of security event
            severity: Severity level (LOW, MEDIUM, HIGH, CRITICAL)
            user_id: ID of user involved
            email_attempted: Email used in attempt
            ip_address: Client IP
            user_agent: Client user agent
            description: Event description
            details: Additional details
            action_taken: Action taken in response
        """
        from app.models.worklog.model import SecurityAuditLog
        
        security_event = SecurityAuditLog(
            event_type=event_type,
            severity=severity,
            user_id=user_id,
            email_attempted=email_attempted,
            ip_address=ip_address,
            user_agent=user_agent,
            description=description,
            details=details,
            action_taken=action_taken,
        )
        
        db.add(security_event)
        await db.commit()
        
        security_logger.warning(
            f"Security event: {event_type} - {description}",
            extra={
                "severity": severity,
                "user_id": user_id,
                "ip_address": ip_address,
            }
        )
    
    @staticmethod
    async def log_login_attempt(
        db: AsyncSession,
        *,
        success: bool,
        email: str,
        ip_address: str,
        user_agent: Optional[str] = None,
        user_id: Optional[int] = None,
        failure_reason: Optional[str] = None,
    ):
        """
        Log a login attempt.
        
        Args:
            db: Database session
            success: Whether login was successful
            email: Email used
            ip_address: Client IP
            user_agent: Client user agent
            user_id: User ID if successful
            failure_reason: Reason for failure if unsuccessful
        """
        event_type = "login_success" if success else "login_failure"
        severity = "LOW" if success else "MEDIUM"
        
        description = f"Login {'successful' if success else 'failed'} for {email}"
        if failure_reason:
            description += f": {failure_reason}"
        
        await AuditLogger.log_security_event(
            db,
            event_type=event_type,
            severity=severity,
            user_id=user_id,
            email_attempted=email,
            ip_address=ip_address,
            user_agent=user_agent,
            description=description,
        )
    
    @staticmethod
    async def log_permission_denied(
        db: AsyncSession,
        *,
        user_id: int,
        resource: str,
        action: str,
        ip_address: str,
    ):
        """
        Log a permission denied event.
        
        Args:
            db: Database session
            user_id: User who was denied
            resource: Resource they tried to access
            action: Action they tried to perform
            ip_address: Client IP
        """
        await AuditLogger.log_security_event(
            db,
            event_type="permission_denied",
            severity="MEDIUM",
            user_id=user_id,
            ip_address=ip_address,
            description=f"Permission denied: {action} on {resource}",
            details={"resource": resource, "action": action},
        )
