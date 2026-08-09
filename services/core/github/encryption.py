"""
Token encryption utilities.

Encrypts GitHub OAuth tokens using AES-256-GCM before storage.
The encryption key is derived from Django's SECRET_KEY via HKDF,
so tokens are tied to the deployment and cannot be extracted from a DB dump alone.

This provides defense-in-depth:
- DB compromise alone doesn't expose tokens
- Tokens are bound to the application secret
- Each token has a unique nonce (IV)
"""

import os

from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.hashes import SHA256
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from django.conf import settings

# Nonce size for AES-GCM (96 bits recommended by NIST)
_NONCE_SIZE = 12


def _derive_key() -> bytes:
    """Derive a 256-bit AES key from Django's SECRET_KEY using HKDF."""
    secret = settings.SECRET_KEY.encode("utf-8")
    hkdf = HKDF(
        algorithm=SHA256(),
        length=32,
        salt=b"clashcode-github-token-v1",
        info=b"github-oauth-token-encryption",
    )
    return hkdf.derive(secret)


def encrypt_token(plaintext: str) -> bytes:
    """
    Encrypt a GitHub token.
    Returns: nonce (12 bytes) + ciphertext + tag (16 bytes)
    """
    key = _derive_key()
    nonce = os.urandom(_NONCE_SIZE)
    aesgcm = AESGCM(key)
    ciphertext = aesgcm.encrypt(nonce, plaintext.encode("utf-8"), None)
    return nonce + ciphertext


def decrypt_token(data: bytes) -> str:
    """
    Decrypt a GitHub token.
    Input: nonce (12 bytes) + ciphertext + tag (16 bytes)
    """
    if not data or len(data) < _NONCE_SIZE + 1:
        raise ValueError("Invalid encrypted token data")

    key = _derive_key()
    nonce = data[:_NONCE_SIZE]
    ciphertext = data[_NONCE_SIZE:]
    aesgcm = AESGCM(key)
    plaintext = aesgcm.decrypt(nonce, ciphertext, None)
    return plaintext.decode("utf-8")
