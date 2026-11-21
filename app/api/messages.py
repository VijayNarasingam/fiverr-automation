"""Message endpoints.

Consumes :class:`app.database.get_session` and the
:class:`app.models.message.Message` model.
Produces: GET /api/messages, POST /api/messages.
"""

from typing import Any

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.models.message import Message, MessageDirection

router = APIRouter(prefix="/api")


@router.get("/messages")
async def list_messages(
    session: AsyncSession = Depends(get_session),
) -> list[dict[str, Any]]:
    """List the most recent messages."""
    result = await session.execute(
        select(Message).order_by(Message.created_at.desc()).limit(50)
    )
    messages = result.scalars().all()
    return [
        {
            "id": message.id,
            "order_id": message.order_id,
            "direction": message.direction,
            "content": message.content,
            "is_auto_replied": message.is_auto_replied,
        }
        for message in messages
    ]


@router.post("/messages")
async def send_message(
    direction: MessageDirection,
    content: str,
    order_id: int | None = None,
    session: AsyncSession = Depends(get_session),
) -> dict[str, Any]:
    """Persist and return a new message."""
    message = Message(direction=direction, content=content, order_id=order_id)
    session.add(message)
    await session.commit()
    await session.refresh(message)
    return {
        "id": message.id,
        "direction": message.direction,
        "content": message.content,
    }
