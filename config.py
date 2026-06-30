"""Configuration helpers for AI Research Office."""

import os
from pathlib import Path

from crewai import LLM


def load_dotenv() -> None:
    env_path = Path(__file__).resolve().parent / ".env"
    if not env_path.exists():
        return

    for raw_line in env_path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


load_dotenv()


PROVIDER_API_KEYS = {
    "Google Gemini": "GEMINI_API_KEY",
    "OpenAI / ChatGPT": "OPENAI_API_KEY",
    "Anthropic Claude": "ANTHROPIC_API_KEY",
}

PROVIDER_PREFIXES = {
    "Google Gemini": "gemini/",
    "OpenAI / ChatGPT": "openai/",
    "Anthropic Claude": "anthropic/",
}

MODEL_CATALOG = {
    "Google Gemini": [
        "gemini-2.5-flash",
        "gemini-2.5-pro",
    ],
    "OpenAI / ChatGPT": [
        "gpt-5.5",
        "gpt-5.4",
        "gpt-5.4-mini",
        "gpt-5.4-nano",
    ],
    "Anthropic Claude": [
        "claude-fable-5",
        "claude-opus-4-8",
        "claude-opus-4-7",
        "claude-sonnet-4-6",
        "claude-haiku-4-5",
    ],
}

DEFAULT_PROVIDER = "Google Gemini"
DEFAULT_MODEL = "gemini-2.5-flash"
AVAILABLE_MODELS = MODEL_CATALOG["Google Gemini"]


def get_gemini_key() -> str | None:
    """Backward-compatible helper for older app.py versions."""
    return os.environ.get("GEMINI_API_KEY")


def get_api_key(provider: str) -> str | None:
    """Read the API key for a provider from the environment."""
    env_name = PROVIDER_API_KEYS[provider]
    return os.environ.get(env_name)


def get_app_password() -> str | None:
    return os.environ.get("APP_PASSWORD")


def get_model_options(provider: str) -> list[str]:
    return MODEL_CATALOG[provider]


def get_llm(provider: str, model_name: str | None = None, api_key: str | None = None) -> LLM:
    """Create the CrewAI LLM wrapper for the selected provider/model."""
    if provider not in PROVIDER_PREFIXES:
        legacy_model = provider
        legacy_key = model_name
        return LLM(
            model=f"gemini/{legacy_model}",
            api_key=legacy_key,
            temperature=0.7,
        )

    key = api_key or get_api_key(provider)
    if not key:
        env_name = PROVIDER_API_KEYS[provider]
        raise ValueError(f"ไม่พบ {env_name} สำหรับ provider {provider}")

    prefix = PROVIDER_PREFIXES[provider]
    return LLM(
        model=f"{prefix}{model_name}",
        api_key=key,
        temperature=0.7,
    )
