"""
Bank token encryption - Security Hardened v8.4.2
ANO TsPS INN 9724016805
"""

import os
import base64
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.backends import default_backend

from app.core.config import settings
from app.core.logging import logger


class TokenEncryption:
    """AES-GCM encryption for sensitive tokens"""

    def __init__(self):
        # Derive key from SECRET_KEY
        key_material = settings.SECRET_KEY.encode()[:32]
        self.key = key_material.ljust(32, b'\0')[:32]
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


token_encryption = TokenEncryption()
