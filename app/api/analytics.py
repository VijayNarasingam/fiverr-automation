"""Analytics endpoints.

Consumes :class:`app.database.get_session` and the :class:`app.models.order.Order`
and :class:`app.models.gig.Gig` models.
Produces: GET /api/analytics/overview, GET /api/analytics/gig-performance.
"""

from typing import Any

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.models.gig import Gig
from app.models.order import Order, OrderStatus
from app.services.analytics_service import analyze_ab_test

router = APIRouter(prefix="/api/analytics")


@router.get("/overview")
async def analytics_overview(
    session: AsyncSession = Depends(get_session),
) -> dict[str, Any]:
    """Return high level counts and revenue."""
    gig_count = (
        await session.execute(select(func.count(Gig.id)))
    ).scalar() or 0
    order_count = (
        await session.execute(select(func.count(Order.id)))
    ).scalar() or 0
    revenue = (
        await session.execute(
            select(func.coalesce(func.sum(Order.amount), 0)).where(
                Order.status.in_([OrderStatus.DELIVERED, OrderStatus.COMPLETED])
            )
        )
    ).scalar() or 0
    return {
        "gigs": gig_count,
        "orders": order_count,
        "revenue_cents": int(revenue),
    }


@router.get("/gig-performance")
async def gig_performance(
    session: AsyncSession = Depends(get_session),
) -> list[dict[str, Any]]:
    """Return per-gig order counts."""
    result = await session.execute(
        select(Gig.id, Gig.title, func.count(Order.id).label("order_count"))
        .outerjoin(Order, Order.gig_id == Gig.id)
        .group_by(Gig.id, Gig.title)
    )
    return [
        {"gig_id": gig_id, "title": title, "order_count": order_count}
        for gig_id, title, order_count in result.all()
    ]


@router.get("/ab-tests/{gig_id}")
async def ab_tests(
    gig_id: int,
    session: AsyncSession = Depends(get_session),
) -> dict[str, Any]:
    """Return A/B test analysis for a gig."""
    return await analyze_ab_test(session, gig_id)
