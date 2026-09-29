from __future__ import annotations

import base64
import hashlib
import json
from typing import Any

from cryptography.fernet import Fernet, InvalidToken

from app.config import get_settings


def _derive_fernet() -> Fernet | None:
    settings = get_settings()
    key = (settings.credentials_fernet_key or "").strip()
    if key:
        try:
            return Fernet(key.encode() if isinstance(key, str) else key)
        except Exception:
            # Allow raw 32-byte secret hashed into a Fernet key
            digest = hashlib.sha256(key.encode()).digest()
            return Fernet(base64.urlsafe_b64encode(digest))
    # Dev fallback: derive from secret_key (not for production)
    digest = hashlib.sha256(settings.secret_key.encode()).digest()
    return Fernet(base64.urlsafe_b64encode(digest))


def encrypt_credentials(data: dict[str, Any]) -> str:
    f = _derive_fernet()
    payload = json.dumps(data, ensure_ascii=False).encode("utf-8")
    assert f is not None
    return f.encrypt(payload).decode("utf-8")


def decrypt_credentials(token: str) -> dict[str, Any]:
    if not token:
        return {}
    f = _derive_fernet()
    assert f is not None
    try:
        raw = f.decrypt(token.encode("utf-8"))
        return json.loads(raw.decode("utf-8"))
    except (InvalidToken, json.JSONDecodeError, ValueError):
        # Backward-compat: allow plain JSON in DB during early setup
        try:
            data = json.loads(token)
            return data if isinstance(data, dict) else {}
        except json.JSONDecodeError:
            return {}


def mask_credentials(data: dict[str, Any]) -> dict[str, Any]:
    masked: dict[str, Any] = {}
    for k, v in data.items():
        if v is None or v == "":
            masked[k] = v
        elif isinstance(v, str) and len(v) <= 4:
            masked[k] = "****"
        elif isinstance(v, str):
            masked[k] = v[:2] + "****" + v[-2:]
        else:
            masked[k] = "****"
    return masked
