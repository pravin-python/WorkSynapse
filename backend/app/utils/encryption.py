"""
LLM Key Encryption Utility
==========================

Secure encryption/decryption for API keys using Fernet symmetric encryption.
"""

import os
import base64
from typing import Optional
from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

from app.core.config import settings


class KeyEncryptionError(Exception):
    """Raised when encryption/decryption fails."""
    pass


class FernetKeyManager:
    """
    Manages Fernet encryption for LLM API keys.
    
    Uses FERNET_SECRET_KEY if provided, otherwise derives a Fernet key 
    from the application's SECRET_KEY using PBKDF2.
    This ensures consistent encryption across app restarts.
    """
    
    _fernet: Optional[Fernet] = None
    _salt: bytes = b"worksynapse_llm_keys_v1"  # Static salt for key derivation
    
    @classmethod
    def _get_fernet(cls) -> Fernet:
        """Get or create the Fernet instance."""
        if cls._fernet is None:
            # Use dedicated FERNET_SECRET_KEY if provided
            if settings.FERNET_SECRET_KEY:
                try:
                    cls._fernet = Fernet(settings.FERNET_SECRET_KEY.encode())
                except Exception:
                    raise KeyEncryptionError(
                        "Invalid FERNET_SECRET_KEY. Generate one with: "
                        "python -c \"from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())\""
                    )
            else:
                # Derive a Fernet-compatible key from SECRET_KEY
                kdf = PBKDF2HMAC(
                    algorithm=hashes.SHA256(),
                    length=32,
                    salt=cls._salt,
                    iterations=100_000,
                )
                key = base64.urlsafe_b64encode(
                    kdf.derive(settings.SECRET_KEY.encode())
                )
                cls._fernet = Fernet(key)
        return cls._fernet
    
    @classmethod
    def encrypt(cls, plaintext: str) -> str:
        """
        Encrypt an API key.
        
        Args:
            plaintext: The raw API key to encrypt
            
        Returns:
            Base64-encoded encrypted key
            
        Raises:
            KeyEncryptionError: If encryption fails
        """
        if not plaintext:
            raise KeyEncryptionError("Cannot encrypt empty key")
        
        try:
            fernet = cls._get_fernet()
            encrypted = fernet.encrypt(plaintext.encode())
            return encrypted.decode()
        except Exception as e:
            raise KeyEncryptionError(f"Encryption failed: {str(e)}")
    
    @classmethod
    def decrypt(cls, encrypted_key: str) -> str:
        """
        Decrypt an encrypted API key.
        
        Args:
            encrypted_key: The encrypted key string
            
        Returns:
            The original plaintext API key
            
        Raises:
            KeyEncryptionError: If decryption fails (invalid key or tampering)
        """
        if not encrypted_key:
            raise KeyEncryptionError("Cannot decrypt empty key")
        
        try:
            fernet = cls._get_fernet()
            decrypted = fernet.decrypt(encrypted_key.encode())
            return decrypted.decode()
        except InvalidToken:
            raise KeyEncryptionError("Invalid or corrupted encrypted key")
        except Exception as e:
            raise KeyEncryptionError(f"Decryption failed: {str(e)}")
    
    @classmethod
    def validate_key_format(cls, api_key: str, provider: str) -> tuple[bool, str]:
        """
        Validate API key format for specific providers.
        
        Args:
            api_key: The API key to validate
            provider: The provider name (openai, gemini, anthropic, etc.)
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not api_key or len(api_key) < 10:
            return False, "API key is too short"
        
        provider = provider.lower()
        
        # Provider-specific validation patterns
        patterns = {
            "openai": {
                "prefix": "sk-",
                "min_length": 40,
                "error": "OpenAI keys should start with 'sk-'"
            },
            "anthropic": {
                "prefix": "sk-ant-",
                "min_length": 40,
                "error": "Anthropic keys should start with 'sk-ant-'"
            },
            "google": {
                "prefix": None,
                "min_length": 30,
                "error": None
            },
            "gemini": {
                "prefix": None,
                "min_length": 30,
                "error": None
            },
            "huggingface": {
                "prefix": "hf_",
                "min_length": 20,
                "error": "HuggingFace keys should start with 'hf_'"
            },
            "cohere": {
                "prefix": None,
                "min_length": 30,
                "error": None
            },
            "groq": {
                "prefix": "gsk_",
                "min_length": 20,
                "error": "Groq keys should start with 'gsk_'"
            },
        }
        
        config = patterns.get(provider, {"prefix": None, "min_length": 20, "error": None})
        
        # Check minimum length
        if len(api_key) < config["min_length"]:
            return False, f"API key should be at least {config['min_length']} characters"
        
        # Check prefix if required
        if config["prefix"] and not api_key.startswith(config["prefix"]):
            return False, config["error"]
        
        return True, ""
    
    @classmethod
    def mask_key(cls, api_key: str, visible_chars: int = 4) -> str:
        """
        Mask an API key for display purposes.
        
        Args:
            api_key: The key to mask
            visible_chars: Number of characters to show at start and end
            
        Returns:
            Masked key like "sk-ab...xyz"
        """
        if not api_key or len(api_key) <= visible_chars * 2:
            return "*" * 10
        
        start = api_key[:visible_chars]
        end = api_key[-visible_chars:]
        return f"{start}...{end}"


# Convenience functions
def encrypt_api_key(api_key: str) -> str:
    """Encrypt an API key."""
    return FernetKeyManager.encrypt(api_key)


def decrypt_api_key(encrypted_key: str) -> str:
    """Decrypt an encrypted API key."""
    return FernetKeyManager.decrypt(encrypted_key)


def validate_api_key(api_key: str, provider: str) -> tuple[bool, str]:
    """Validate API key format."""
    return FernetKeyManager.validate_key_format(api_key, provider)


def mask_api_key(api_key: str) -> str:
    """Mask API key for display."""
    return FernetKeyManager.mask_key(api_key)
