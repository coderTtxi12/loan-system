"""PII (Personally Identifiable Information) encryption utilities."""
import base64
import hashlib
import logging
from typing import Optional

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

from app.core.config import settings

logger = logging.getLogger(__name__)


class PIIEncryption:
    """
    Handles encryption and decryption of PII data.
    
    Uses Fernet (symmetric encryption) with a key derived from JWT_SECRET.
    This ensures PII is encrypted at rest in the database.
    """

    _instance: Optional["PIIEncryption"] = None
    _fernet: Optional[Fernet] = None

    def __new__(cls) -> "PIIEncryption":
        """Singleton pattern for encryption instance."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def _get_fernet(self) -> Fernet:
        """
        Get or create Fernet instance.
        
        Derives encryption key from JWT_SECRET using PBKDF2.
        """
        if self._fernet is None:
            # Derive a 32-byte key from JWT_SECRET
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=b"loan_pii_salt_v1",  # Fixed salt for consistency
                iterations=100000,
            )
            key = base64.urlsafe_b64encode(
                kdf.derive(settings.JWT_SECRET.encode())
            )
            self._fernet = Fernet(key)
        return self._fernet

    def encrypt(self, plaintext: str) -> str:
        """
        Encrypt PII data.
        
        Args:
            plaintext: Plain text to encrypt
            
        Returns:
            Encrypted string (base64 encoded)
        """
        if not plaintext:
            return ""
        
        try:
            fernet = self._get_fernet()
            encrypted = fernet.encrypt(plaintext.encode("utf-8"))
            return encrypted.decode("utf-8")
        except Exception as e:
            logger.error(f"Failed to encrypt PII: {e}")
            raise ValueError(f"Encryption failed: {e}")

    def decrypt(self, ciphertext: str) -> str:
        """
        Decrypt PII data.
        
        Args:
            ciphertext: Encrypted string to decrypt
            
        Returns:
            Decrypted plain text
        """
        if not ciphertext:
            return ""
        
        try:
            fernet = self._get_fernet()
            decrypted = fernet.decrypt(ciphertext.encode("utf-8"))
            return decrypted.decode("utf-8")
        except Exception as e:
            logger.error(f"Failed to decrypt PII: {e}")
            raise ValueError(f"Decryption failed: {e}")

    @staticmethod
    def hash_document(document_number: str, country_code: str) -> str:
        """
        Create a searchable hash of document number.
        
        This allows lookups without decrypting the actual document.
        
        Args:
            document_number: The document number
            country_code: The country code
            
        Returns:
            SHA256 hash string
        """
        combined = f"{country_code}:{document_number}".upper().strip()
        return hashlib.sha256(combined.encode()).hexdigest()


# Global instance
pii_encryption = PIIEncryption()


def encrypt_pii(data: str) -> str:
    """
    Encrypt PII data (convenience function).
    
    Args:
        data: Plain text to encrypt
        
    Returns:
        Encrypted string
    """
    return pii_encryption.encrypt(data)


def decrypt_pii(data: str) -> str:
    """
    Decrypt PII data (convenience function).
    
    Args:
        data: Encrypted string to decrypt
        
    Returns:
        Decrypted plain text
    """
    return pii_encryption.decrypt(data)


def hash_document(document_number: str, country_code: str) -> str:
    """
    Hash document for searchable lookup (convenience function).
    
    Args:
        document_number: The document number
        country_code: The country code
        
    Returns:
        SHA256 hash string
    """
    return PIIEncryption.hash_document(document_number, country_code)
