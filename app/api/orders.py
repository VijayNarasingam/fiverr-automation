"""Order endpoints.

Consumes :class:`app.database.get_session`, the
:class:`app.models.order.Order` model and
:class:`app.models.order.OrderStatus` enum.
Produces: GET /api/orders, POST /api/orders/{order_id}/status.
"""

from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.models.order import Order, OrderStatus

router = APIRouter(prefix="/api")


@router.get("/orders")
async def list_orders(
    session: AsyncSession = Depends(get_session),
) -> list[dict[str, Any]]:
    """List every persisted order."""
    result = await session.execute(select(Order))
    orders = result.scalars().all()
    return [
        {
            "id": order.id,
            "fiverr_order_id": order.fiverr_order_id,
            "gig_id": order.gig_id,
            "buyer_username": order.buyer_username,
            "amount": order.amount,
            "status": order.status,
        }
        for order in orders
    ]


@router.post("/orders/{order_id}/status")
async def update_order_status(
    order_id: int,
    status: OrderStatus,
    session: AsyncSession = Depends(get_session),
) -> dict[str, Any]:
    """Update the status of an existing order."""
    order = await session.get(Order, order_id)
    if order is None:
        raise HTTPException(status_code=404, detail="Order not found")
    order.status = status
    await session.commit()
    return {"id": order.id, "status": order.status}
