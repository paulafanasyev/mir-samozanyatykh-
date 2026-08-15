"""
Encryption service for Mir Samozanyatykh v8.2
Uses Fernet (AES-128-CBC + HMAC) for authenticated encryption
"""

import os
import base64
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2

# ✅ Ключ ТОЛЬКО из переменной окружения
_BANK_ENCRYPTION_KEY = os.environ.get("BANK_ENCRYPTION_KEY")
if not _BANK_ENCRYPTION_KEY:
    # Для разработки — warning, но не fallback на известное значение
    import warnings
    warnings.warn("BANK_ENCRYPTION_KEY not set. Bank encryption will fail.")
    _fernet = None
else:
    # Fernet key must be 32 bytes base64-encoded
    key_bytes = _BANK_ENCRYPTION_KEY.encode() if isinstance(_BANK_ENCRYPTION_KEY, str) else _BANK_ENCRYPTION_KEY
    if len(base64.urlsafe_b64decode(key_bytes + b'=' * (-len(key_bytes) % 4))) != 32:
        raise ValueError("BANK_ENCRYPTION_KEY must be 32 bytes base64-encoded (use Fernet.generate_key())")
    _fernet = Fernet(key_bytes)


def encrypt_bank_token(plaintext: str) -> str:
    """
    Encrypt bank API token with authenticated encryption (Fernet).
    Returns base64-encoded ciphertext.
    """
    if not plaintext:
        return ""
    if _fernet is None:
        raise RuntimeError("BANK_ENCRYPTION_KEY not configured")

    encrypted = _fernet.encrypt(plaintext.encode("utf-8"))
    return encrypted.decode("utf-8")


def decrypt_bank_token(ciphertext: str) -> str:
    """
    Decrypt bank API token.
    """
    if not ciphertext:
        return ""
    if _fernet is None:
        raise RuntimeError("BANK_ENCRYPTION_KEY not configured")

    decrypted = _fernet.decrypt(ciphertext.encode("utf-8"))
    return decrypted.decode("utf-8")


def rotate_encryption_key(plaintext: str, new_key: str) -> str:
    """
    Re-encrypt data with new key (for key rotation).
    1. Decrypt with old key
    2. Encrypt with new key
    """
    # Decrypt with current key
    decrypted = decrypt_bank_token(plaintext)

    # Temporarily switch to new key
    global _fernet
    old_fernet = _fernet
    _fernet = Fernet(new_key.encode() if isinstance(new_key, str) else new_key)

    try:
        reencrypted = encrypt_bank_token(decrypted)
        return reencrypted
    finally:
        _fernet = old_fernet


def generate_encryption_key() -> str:
    """Generate new Fernet key"""
    return Fernet.generate_key().decode("utf-8")
