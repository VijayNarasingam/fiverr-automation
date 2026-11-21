"""Settings endpoints.

Consumes :class:`app.config.settings`.
Produces: GET /api/settings, POST /api/settings.
"""

from typing import Any

from fastapi import APIRouter

from app.config import settings

router = APIRouter(prefix="/api")

_SENSITIVE_KEYS = {
    "FIVERR_PASSWORD",
    "SMTP_PASSWORD",
    "GOOGLE_SHEETS_CREDENTIALS_JSON",
    "DISCORD_WEBHOOK_URL",
    "SLACK_WEBHOOK_URL",
    "SECRET_KEY",
    "PROXY_API_URLS",
}


@router.get("/settings")
async def get_settings() -> dict[str, Any]:
    """Return current settings, masking sensitive values."""
    data = settings.model_dump()
    data["discord_configured"] = bool(data.get("DISCORD_WEBHOOK_URL"))
    for key in _SENSITIVE_KEYS:
        if data.get(key):
            data[key] = "***"
    return data


@router.post("/settings")
async def update_settings(updates: dict[str, Any]) -> dict[str, Any]:
    """Accept settings updates (acknowledges recognized keys)."""
    accepted = [key for key in updates if hasattr(settings, key)]
    return {"status": "accepted", "updated": accepted}
