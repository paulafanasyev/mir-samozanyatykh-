"""
Bank token encryption - Security Hardened v8.4.3
ANO TsPS INN 9724016805
"""

import os
import base64
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from app.core.config import settings
from app.core.logging import logger


class TokenEncryption:
    """AES-GCM encryption for sensitive tokens"""

    def __init__(self):
        if not settings.BANK_ENCRYPTION_KEY:
            raise RuntimeError("BANK_ENCRYPTION_KEY must be configured")
        try:
            import base64
            self.key = base64.urlsafe_b64decode(settings.BANK_ENCRYPTION_KEY.encode())
        except Exception as exc:
            raise RuntimeError("BANK_ENCRYPTION_KEY must be URL-safe base64") from exc
        if len(self.key) != 32:
            raise RuntimeError("BANK_ENCRYPTION_KEY must decode to exactly 32 bytes")
        self.aesgcm = AESGCM(self.key)

    def encrypt(self, plaintext: str) -> str:
        """Encrypt token with AES-GCM"""
        if not plaintext:
            return ""

        nonce = os.urandom(12)
        ciphertext = self.aesgcm.encrypt(
            nonce,
            plaintext.encode(),
            None
        )
        # Store nonce + ciphertext as base64
        return base64.b64encode(nonce + ciphertext).decode()

    def decrypt(self, encrypted: str) -> str:
        """Decrypt token"""
        if not encrypted:
            return ""

        try:
            data = base64.b64decode(encrypted.encode())
            nonce = data[:12]
            ciphertext = data[12:]

            plaintext = self.aesgcm.decrypt(nonce, ciphertext, None)
            return plaintext.decode()
        except Exception as e:
            logger.error(f"Token decryption failed: {e}")
            raise ValueError("Invalid encrypted token")


_token_encryption = None

def get_token_encryption() -> TokenEncryption:
    global _token_encryption
    if _token_encryption is None:
        _token_encryption = TokenEncryption()
    return _token_encryption

