"""Log endpoints.

Produces: GET /api/logs (empty list placeholder),
POST /api/logs/{log_id}/replay (placeholder).
"""

from typing import Any

from fastapi import APIRouter

router = APIRouter(prefix="/api")


@router.get("/logs")
async def list_logs() -> list[dict[str, Any]]:
    """Return logs. Placeholder: no log store wired yet."""
    return []


@router.post("/logs/{log_id}/replay")
async def replay_log(log_id: int) -> dict[str, Any]:
    """Replay a log entry. Placeholder implementation."""
    return {"log_id": log_id, "status": "replayed", "note": "placeholder"}
