"""Simple file-backed user authentication for Streamlit."""

from __future__ import annotations

import hashlib
import hmac
import json
import os
import secrets
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path


DATA_DIR = Path(__file__).resolve().parent / "data"
USERS_PATH = DATA_DIR / "users.json"
API_KEY_SECRET_PATH = DATA_DIR / ".api_key_secret"
PBKDF2_ITERATIONS = 260_000


@dataclass
class AuthResult:
    ok: bool
    message: str


def _load_users() -> dict:
    if not USERS_PATH.exists():
        return {"users": {}}
    return json.loads(USERS_PATH.read_text(encoding="utf-8-sig"))


def _save_users(data: dict) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    USERS_PATH.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def _normalize_username(username: str) -> str:
    return username.strip().lower()


def _fernet_key() -> bytes | None:
    try:
        from cryptography.fernet import Fernet
    except ImportError:
        return None

    configured_secret = os.environ.get("API_KEY_STORAGE_SECRET") or os.environ.get("APP_PASSWORD")
    if configured_secret:
        digest = hashlib.sha256(configured_secret.encode("utf-8")).digest()
        import base64

        return base64.urlsafe_b64encode(digest)

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if API_KEY_SECRET_PATH.exists():
        key = API_KEY_SECRET_PATH.read_text(encoding="utf-8").strip().encode("utf-8")
        try:
            Fernet(key)
            return key
        except Exception:
            pass

    key = Fernet.generate_key()
    API_KEY_SECRET_PATH.write_text(key.decode("utf-8"), encoding="utf-8")
    return key


def _protect_secret(value: str) -> dict[str, str]:
    clean_value = value.strip()
    key = _fernet_key()
    if key:
        from cryptography.fernet import Fernet

        return {
            "scheme": "fernet",
            "value": Fernet(key).encrypt(clean_value.encode("utf-8")).decode("utf-8"),
        }

    return {"scheme": "plain", "value": clean_value}


def _unprotect_secret(payload: object) -> str | None:
    if isinstance(payload, str):
        return payload.strip() or None
    if not isinstance(payload, dict):
        return None

    scheme = payload.get("scheme")
    value = payload.get("value")
    if not isinstance(value, str) or not value:
        return None

    if scheme == "fernet":
        key = _fernet_key()
        if not key:
            return None
        try:
            from cryptography.fernet import Fernet

            return Fernet(key).decrypt(value.encode("utf-8")).decode("utf-8").strip() or None
        except Exception:
            return None

    if scheme == "plain":
        return value.strip() or None

    return None


def _hash_password(password: str, salt_hex: str | None = None) -> tuple[str, str]:
    salt = bytes.fromhex(salt_hex) if salt_hex else secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        PBKDF2_ITERATIONS,
    )
    return salt.hex(), digest.hex()


def user_count() -> int:
    return len(_load_users().get("users", {}))


def create_user(username: str, password: str) -> AuthResult:
    normalized = _normalize_username(username)
    if len(normalized) < 3:
        return AuthResult(False, "ชื่อผู้ใช้ต้องมีอย่างน้อย 3 ตัวอักษร")
    if len(password) < 8:
        return AuthResult(False, "รหัสผ่านต้องมีอย่างน้อย 8 ตัวอักษร")

    data = _load_users()
    users = data.setdefault("users", {})
    if normalized in users:
        return AuthResult(False, "มีชื่อผู้ใช้นี้แล้ว")

    salt, password_hash = _hash_password(password)
    users[normalized] = {
        "salt": salt,
        "password_hash": password_hash,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    _save_users(data)
    return AuthResult(True, "สมัครสมาชิกสำเร็จ")


def authenticate(username: str, password: str) -> AuthResult:
    normalized = _normalize_username(username)
    user = _load_users().get("users", {}).get(normalized)
    if not user:
        return AuthResult(False, "ชื่อผู้ใช้หรือรหัสผ่านไม่ถูกต้อง")

    _salt, attempted_hash = _hash_password(password, user["salt"])
    if not hmac.compare_digest(attempted_hash, user["password_hash"]):
        return AuthResult(False, "ชื่อผู้ใช้หรือรหัสผ่านไม่ถูกต้อง")

    return AuthResult(True, normalized)


def get_user_api_keys(username: str) -> dict[str, str]:
    normalized = _normalize_username(username)
    user = _load_users().get("users", {}).get(normalized, {})
    saved_keys = user.get("api_keys", {})
    if not isinstance(saved_keys, dict):
        return {}

    restored: dict[str, str] = {}
    for provider, payload in saved_keys.items():
        value = _unprotect_secret(payload)
        if value:
            restored[provider] = value
    return restored


def save_user_api_key(username: str, provider: str, api_key: str) -> AuthResult:
    normalized = _normalize_username(username)
    data = _load_users()
    user = data.get("users", {}).get(normalized)
    if not user:
        return AuthResult(False, "ไม่พบบัญชีผู้ใช้สำหรับบันทึก API key")

    clean_key = api_key.strip()
    saved_keys = user.setdefault("api_keys", {})
    if clean_key:
        saved_keys[provider] = _protect_secret(clean_key)
    else:
        saved_keys.pop(provider, None)
    user["api_keys_updated_at"] = datetime.now(timezone.utc).isoformat()
    _save_users(data)
    return AuthResult(True, "บันทึก API key แล้ว")


def clear_user_api_keys(username: str) -> AuthResult:
    normalized = _normalize_username(username)
    data = _load_users()
    user = data.get("users", {}).get(normalized)
    if not user:
        return AuthResult(False, "ไม่พบบัญชีผู้ใช้สำหรับล้าง API key")

    user["api_keys"] = {}
    user["api_keys_updated_at"] = datetime.now(timezone.utc).isoformat()
    _save_users(data)
    return AuthResult(True, "ล้าง API keys ที่บันทึกไว้แล้ว")


def get_user_line_settings(username: str) -> dict[str, str]:
    normalized = _normalize_username(username)
    user = _load_users().get("users", {}).get(normalized, {})
    saved_settings = user.get("line_settings", {})
    if not isinstance(saved_settings, dict):
        return {}

    restored: dict[str, str] = {}
    for key, payload in saved_settings.items():
        value = _unprotect_secret(payload)
        if value:
            restored[key] = value
    return restored


def save_user_line_settings(
    username: str,
    channel_access_token: str,
    recipient_id: str,
) -> AuthResult:
    normalized = _normalize_username(username)
    data = _load_users()
    user = data.get("users", {}).get(normalized)
    if not user:
        return AuthResult(False, "ไม่พบบัญชีผู้ใช้สำหรับบันทึก LINE")

    token = channel_access_token.strip()
    recipient = recipient_id.strip()
    line_settings = user.setdefault("line_settings", {})
    if token:
        line_settings["channel_access_token"] = _protect_secret(token)
    else:
        line_settings.pop("channel_access_token", None)
    if recipient:
        line_settings["recipient_id"] = _protect_secret(recipient)
    else:
        line_settings.pop("recipient_id", None)
    user["line_settings_updated_at"] = datetime.now(timezone.utc).isoformat()
    _save_users(data)
    return AuthResult(True, "บันทึกการตั้งค่า LINE แล้ว")


def clear_user_line_settings(username: str) -> AuthResult:
    normalized = _normalize_username(username)
    data = _load_users()
    user = data.get("users", {}).get(normalized)
    if not user:
        return AuthResult(False, "ไม่พบบัญชีผู้ใช้สำหรับล้างการตั้งค่า LINE")

    user["line_settings"] = {}
    user["line_settings_updated_at"] = datetime.now(timezone.utc).isoformat()
    _save_users(data)
    return AuthResult(True, "ล้างการตั้งค่า LINE แล้ว")
