"""Server-sent events endpoint.

Produces: GET /api/events (EventSourceResponse heartbeat).
"""

import asyncio
from typing import Any

from fastapi import APIRouter
from sse_starlette import EventSourceResponse

router = APIRouter(prefix="/api")


async def _event_stream() -> Any:
    while True:
        yield {"event": "heartbeat", "data": {"ok": True}}
        await asyncio.sleep(5)


@router.get("/events")
async def events():
    """Stream heartbeat events to connected clients."""
    return EventSourceResponse(_event_stream())
