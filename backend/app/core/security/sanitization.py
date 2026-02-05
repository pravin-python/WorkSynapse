"""
WorkSynapse Input Sanitization Module
=====================================
Input validation and sanitization utilities for security.

Security Features:
- XSS prevention
- SQL injection protection
- Input validation
- URL sanitization
- Email validation
"""
import re
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class InputSanitizer:
    """
    Sanitize user inputs to prevent XSS and injection attacks.
    """
    
    # Patterns to remove
    DANGEROUS_PATTERNS = [
        r'<script[^>]*>.*?</script>',  # Script tags
        r'javascript:',                  # JavaScript URLs
        r'on\w+\s*=',                   # Event handlers
        r'<iframe[^>]*>',               # Iframes
        r'<object[^>]*>',               # Object tags
        r'<embed[^>]*>',                # Embed tags
    ]
    
    @classmethod
    def sanitize_string(cls, value: str) -> str:
        """
        Sanitize a string input.
        
        Args:
            value: Raw input string
            
        Returns:
            Sanitized string
        """
        if not value:
            return value
        
        sanitized = value
        for pattern in cls.DANGEROUS_PATTERNS:
            sanitized = re.sub(pattern, '', sanitized, flags=re.IGNORECASE | re.DOTALL)
        
        # HTML entity encode special characters
        sanitized = sanitized.replace('<', '&lt;').replace('>', '&gt;')
        
        return sanitized.strip()
    
    @classmethod
    def sanitize_email(cls, email: str) -> str:
        """
        Validate and sanitize email.
        
        Args:
            email: Raw email string
            
        Returns:
            Validated and normalized email
            
        Raises:
            ValueError: If email format is invalid
        """
        email = email.lower().strip()
        
        # Basic email validation regex
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, email):
            raise ValueError("Invalid email format")
        
        return email
    
    @classmethod
    def sanitize_url(cls, url: str) -> str:
        """
        Validate and sanitize URL.
        
        Args:
            url: Raw URL string
            
        Returns:
            Validated URL
            
        Raises:
            ValueError: If URL is invalid or uses dangerous scheme
        """
        url = url.strip()
        
        # Check for dangerous schemes
        if any(scheme in url.lower() for scheme in ['javascript:', 'data:', 'vbscript:']):
            raise ValueError("Invalid URL scheme")
        
        # Basic URL validation
        url_pattern = r'^https?://[^\s/$.?#].[^\s]*$'
        if not re.match(url_pattern, url, re.IGNORECASE):
            raise ValueError("Invalid URL format")
        
        return url
    
    @classmethod
    def sanitize_filename(cls, filename: str) -> str:
        """
        Sanitize a filename to prevent path traversal attacks.
        
        Args:
            filename: Raw filename
            
        Returns:
            Safe filename
        """
        # Remove path separators and traversal patterns
        sanitized = re.sub(r'[/\\]', '', filename)
        sanitized = sanitized.replace('..', '')
        
        # Only allow alphanumeric, dash, underscore, and dot
        sanitized = re.sub(r'[^a-zA-Z0-9._-]', '_', sanitized)
        
        return sanitized


class SQLInjectionProtection:
    """
    Additional SQL injection protection utilities.
    
    Note: SQLAlchemy ORM already provides parameterized queries,
    but this adds extra validation for dynamic queries.
    """
    
    # SQL keywords that shouldn't appear in user input
    DANGEROUS_KEYWORDS = [
        'SELECT', 'INSERT', 'UPDATE', 'DELETE', 'DROP', 'TRUNCATE',
        'CREATE', 'ALTER', 'GRANT', 'REVOKE', 'UNION', 'OR 1=1',
        'OR 1 = 1', '--', '/*', '*/', 'EXEC', 'EXECUTE',
    ]
    
    @classmethod
    def is_safe_input(cls, value: str) -> bool:
        """
        Check if input is safe from SQL injection.
        
        Args:
            value: User input string
            
        Returns:
            bool: True if input appears safe
        """
        upper_value = value.upper()
        for keyword in cls.DANGEROUS_KEYWORDS:
            if keyword in upper_value:
                return False
        return True
    
    @classmethod
    def sanitize_identifier(cls, identifier: str) -> str:
        """
        Sanitize a database identifier (table/column name).
        
        Only allow alphanumeric and underscores.
        
        Args:
            identifier: Raw identifier string
            
        Returns:
            Sanitized identifier
            
        Raises:
            ValueError: If identifier is invalid
        """
        sanitized = re.sub(r'[^a-zA-Z0-9_]', '', identifier)
        if not sanitized or sanitized[0].isdigit():
            raise ValueError("Invalid identifier")
        return sanitized
    
    @classmethod
    def validate_order_by(cls, column: str, allowed_columns: list) -> str:
        """
        Validate an ORDER BY column against allowed list.
        
        Args:
            column: Requested column name
            allowed_columns: List of safe column names
            
        Returns:
            Validated column name
            
        Raises:
            ValueError: If column not in allowed list
        """
        if column not in allowed_columns:
            raise ValueError(f"Invalid sort column: {column}")
        return column


class XSSProtection:
    """
    XSS (Cross-Site Scripting) protection utilities.
    """
    
    @staticmethod
    def encode_html(text: str) -> str:
        """
        HTML entity encode a string.
        
        Args:
            text: Raw text
            
        Returns:
            HTML-safe text
        """
        if not text:
            return text
        
        return (text
            .replace('&', '&amp;')
            .replace('<', '&lt;')
            .replace('>', '&gt;')
            .replace('"', '&quot;')
            .replace("'", '&#x27;')
        )
    
    @staticmethod
    def strip_tags(html: str) -> str:
        """
        Remove all HTML tags from a string.
        
        Args:
            html: HTML string
            
        Returns:
            Plain text
        """
        return re.sub(r'<[^>]+>', '', html)
