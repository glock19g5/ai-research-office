"""FastAPI application entrypoint (WB-0.3).

Provides a health endpoint only. No AI, no database, no side effects.
"""

from __future__ import annotations

from fastapi import FastAPI

from app import __version__
from app.config import get_settings

settings = get_settings()

app = FastAPI(
    title="AIO-1.1 Backend",
    version=__version__,
    description="Phase 1 foundation service (separated from the Streamlit UI).",
)


@app.get("/health", tags=["ops"])
def health() -> dict[str, str]:
    """Liveness/readiness probe. Must not depend on AI or DB in Phase 1."""
    return {
        "status": "ok",
        "service": settings.service_name,
        "version": __version__,
        "env": settings.app_env,
    }


@app.get("/", tags=["ops"])
def root() -> dict[str, str]:
    return {"service": settings.service_name, "version": __version__}
