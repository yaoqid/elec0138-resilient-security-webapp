"""
AES-256 field-level encryption for sensitive patient data at rest.

Uses Fernet (AES-128-CBC under the hood via the cryptography library) which
provides authenticated encryption.  The key is derived from a master password
using PBKDF2-HMAC-SHA256 so it can be reproduced deterministically from a
single secret stored outside the database.

In production the master secret would live in an HSM or secrets manager.
For this coursework demo it is read from an environment variable or falls
back to a file-based key.
"""

import base64
import os
from pathlib import Path

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

_KEY_FILE = Path(__file__).resolve().parent.parent / "instance" / ".encryption_key"
_SALT = b"hospital-demo-salt-2026"  # Fixed salt for demo reproducibility


def _derive_key(master_secret: str) -> bytes:
    """Derive a Fernet-compatible key from a master secret using PBKDF2."""
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=_SALT,
        iterations=480_000,
    )
    return base64.urlsafe_b64encode(kdf.derive(master_secret.encode()))


def _get_master_secret() -> str:
    """Return the master encryption secret (env var > key file > default)."""
    secret = os.environ.get("ENCRYPTION_KEY")
    if secret:
        return secret
    if _KEY_FILE.exists():
        return _KEY_FILE.read_text().strip()
    # First run – generate and persist a key
    secret = Fernet.generate_key().decode()
    _KEY_FILE.write_text(secret)
    return secret


_cached_fernet: Fernet | None = None


def get_fernet() -> Fernet:
    """Return a ready-to-use Fernet cipher (cached after first call)."""
    global _cached_fernet
    if _cached_fernet is None:
        _cached_fernet = Fernet(_derive_key(_get_master_secret()))
    return _cached_fernet


def encrypt_field(value: str | None) -> str | None:
    """Encrypt a single text value.  Returns base64-encoded ciphertext."""
    if value is None:
        return None
    return get_fernet().encrypt(value.encode()).decode()


def decrypt_field(token: str | None) -> str | None:
    """Decrypt a single Fernet token back to plaintext."""
    if token is None:
        return None
    try:
        return get_fernet().decrypt(token.encode()).decode()
    except Exception:
        # If decryption fails (e.g. data was stored before encryption was
        # enabled), return the raw value so the app doesn't crash.
        return token
