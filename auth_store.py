"""Simple file-backed user authentication for Streamlit."""

from __future__ import annotations

import hashlib
import hmac
import json
import secrets
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path


DATA_DIR = Path(__file__).resolve().parent / "data"
USERS_PATH = DATA_DIR / "users.json"
PBKDF2_ITERATIONS = 260_000


@dataclass
class AuthResult:
    ok: bool
    message: str


def _load_users() -> dict:
    if not USERS_PATH.exists():
        return {"users": {}}
    return json.loads(USERS_PATH.read_text(encoding="utf-8"))


def _save_users(data: dict) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    USERS_PATH.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def _normalize_username(username: str) -> str:
    return username.strip().lower()


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
