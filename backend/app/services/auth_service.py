"""
WorkSynapse Authentication Service
==================================
Service layer for authentication operations including:
- User login/logout
- Token management
- Password management
- Session handling
"""

from typing import Optional, Tuple
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import logging

from app.core.config import settings
from app.core.security import (
    verify_password,
    get_password_hash,
    create_access_token,
    create_refresh_token,
    create_token_pair,
    decode_token,
    validate_password_strength,
    TokenPair,
    TokenPayload,
)
from app.core.security.audit import AuditLogger
from app.models.user.model import User, UserStatus

logger = logging.getLogger(__name__)


class AuthenticationError(Exception):
    """Raised when authentication fails."""
    pass


class AuthService:
    """
    Authentication service for handling user authentication.
    
    Usage:
        auth_service = AuthService()
        tokens = await auth_service.login(db, "user@example.com", "password")
    """
    
    async def login(
        self,
        db: AsyncSession,
        email: str,
        password: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> Tuple[User, TokenPair]:
        """
        Authenticate a user and return tokens.
        
        Args:
            db: Database session
            email: User email
            password: Plain text password
            ip_address: Client IP for logging
            user_agent: Client user agent for logging
            
        Returns:
            Tuple of (User, TokenPair)
            
        Raises:
            AuthenticationError: If authentication fails
        """
        # Find user
        stmt = select(User).where(User.email == email.lower())
        result = await db.execute(stmt)
        user = result.scalars().first()
        
        if not user:
            # Log failed attempt
            await AuditLogger.log_login_attempt(
                db,
                success=False,
                email=email,
                ip_address=ip_address or "unknown",
                user_agent=user_agent,
                failure_reason="User not found",
            )
            raise AuthenticationError("Invalid email or password")
        
        # Check password
        if not verify_password(password, user.hashed_password):
            # Record failed attempt
            user.record_failed_login()
            await db.commit()
            
            await AuditLogger.log_login_attempt(
                db,
                success=False,
                email=email,
                ip_address=ip_address or "unknown",
                user_agent=user_agent,
                user_id=user.id,
                failure_reason="Invalid password",
            )
            raise AuthenticationError("Invalid email or password")
        
        # Check if user is active
        if not user.is_active:
            await AuditLogger.log_login_attempt(
                db,
                success=False,
                email=email,
                ip_address=ip_address or "unknown",
                user_agent=user_agent,
                user_id=user.id,
                failure_reason="Account disabled",
            )
            raise AuthenticationError("Account is disabled")
        
        # Check if user is locked
        if hasattr(user, 'is_locked') and user.is_locked():
            await AuditLogger.log_login_attempt(
                db,
                success=False,
                email=email,
                ip_address=ip_address or "unknown",
                user_agent=user_agent,
                user_id=user.id,
                failure_reason="Account locked",
            )
            raise AuthenticationError("Account is locked due to too many failed attempts")
        
        # Generate tokens
        role = user.role.value if hasattr(user.role, 'value') else str(user.role)
        tokens = create_token_pair(str(user.id), role)
        
        # Record successful login
        user.record_login()
        await db.commit()
        
        await AuditLogger.log_login_attempt(
            db,
            success=True,
            email=email,
            ip_address=ip_address or "unknown",
            user_agent=user_agent,
            user_id=user.id,
        )
        
        logger.info(f"User logged in: {user.email}")
        
        return user, tokens
    
    async def refresh_token(
        self,
        db: AsyncSession,
        refresh_token: str,
    ) -> TokenPair:
        """
        Refresh access token using a refresh token.
        
        Args:
            db: Database session
            refresh_token: Valid refresh token
            
        Returns:
            New TokenPair
            
        Raises:
            AuthenticationError: If refresh token is invalid
        """
        payload = decode_token(refresh_token)
        
        if not payload or payload.type != "refresh":
            raise AuthenticationError("Invalid refresh token")
        
        # Check expiration
        if datetime.utcnow() > payload.exp:
            raise AuthenticationError("Refresh token has expired")
        
        # Get user
        stmt = select(User).where(User.id == int(payload.sub))
        result = await db.execute(stmt)
        user = result.scalars().first()
        
        if not user or not user.is_active:
            raise AuthenticationError("User not found or inactive")
        
        # Generate new tokens
        role = user.role.value if hasattr(user.role, 'value') else str(user.role)
        return create_token_pair(str(user.id), role)
    
    async def change_password(
        self,
        db: AsyncSession,
        user: User,
        current_password: str,
        new_password: str,
    ) -> bool:
        """
        Change user password.
        
        Args:
            db: Database session
            user: User object
            current_password: Current password for verification
            new_password: New password to set
            
        Returns:
            True if successful
            
        Raises:
            AuthenticationError: If current password is wrong
            ValueError: If new password doesn't meet requirements
        """
        # Verify current password
        if not verify_password(current_password, user.hashed_password):
            raise AuthenticationError("Current password is incorrect")
        
        # Validate new password
        is_valid, error = validate_password_strength(new_password)
        if not is_valid:
            raise ValueError(error)
        
        # Update password
        user.hashed_password = get_password_hash(new_password)
        await db.commit()
        
        logger.info(f"Password changed for user: {user.email}")
        return True
    
    async def reset_password(
        self,
        db: AsyncSession,
        user: User,
        new_password: str,
    ) -> bool:
        """
        Reset user password (admin operation).
        
        Args:
            db: Database session
            user: User object
            new_password: New password to set
            
        Returns:
            True if successful
            
        Raises:
            ValueError: If new password doesn't meet requirements
        """
        # Validate new password
        is_valid, error = validate_password_strength(new_password)
        if not is_valid:
            raise ValueError(error)
        
        # Update password
        user.hashed_password = get_password_hash(new_password)
        # Force password change on next login
        if hasattr(user, 'force_password_change'):
            user.force_password_change = True
        
        await db.commit()
        
        logger.info(f"Password reset for user: {user.email}")
        return True
    
    async def logout(
        self,
        db: AsyncSession,
        user: User,
        ip_address: Optional[str] = None,
    ) -> bool:
        """
        Log out a user.
        
        This can be extended to invalidate tokens, clear sessions, etc.
        
        Args:
            db: Database session
            user: User to log out
            ip_address: Client IP for logging
            
        Returns:
            True if successful
        """
        # In a full implementation, this might:
        # - Add token to blacklist
        # - Clear session data
        # - Update last activity
        
        logger.info(f"User logged out: {user.email}")
        return True


# Singleton instance
auth_service = AuthService()
