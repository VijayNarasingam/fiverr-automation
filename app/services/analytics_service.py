"""Analytics service layer for the Fiverr Automation Agent.

Consumes the :class:`app.models.gig.Gig` and :class:`app.models.order.Order`
models plus an async SQLAlchemy session.

Functions exposed:
- compute_overview(session) -> dict
- compute_gig_performance(session) -> list[dict]
- analyze_ab_test(session, gig_id) -> dict
"""

import logging
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.gig import Gig, GigStatus
from app.models.order import Order, OrderStatus

logger = logging.getLogger(__name__)

# Order statuses that count as completed/revenue-generating.
REVENUE_STATUSES = [OrderStatus.DELIVERED, OrderStatus.COMPLETED]


async def compute_overview(session: AsyncSession) -> dict[str, Any]:
    """Return high level counts and revenue.

    Counts total and published gigs, total and completed orders, and sums
    revenue (in cents) across delivered/completed orders.
    """
    total_gigs = (
        await session.execute(select(func.count(Gig.id)))
    ).scalar() or 0
    published_gigs = (
        await session.execute(
            select(func.count(Gig.id)).where(Gig.status == GigStatus.PUBLISHED)
        )
    ).scalar() or 0
    total_orders = (
        await session.execute(select(func.count(Order.id)))
    ).scalar() or 0
    completed_orders = (
        await session.execute(
            select(func.count(Order.id)).where(Order.status.in_(REVENUE_STATUSES))
        )
    ).scalar() or 0
    revenue = (
        await session.execute(
            select(func.coalesce(func.sum(Order.amount), 0)).where(
                Order.status.in_(REVENUE_STATUSES)
            )
        )
    ).scalar() or 0

    return {
        "total_gigs": int(total_gigs),
        "published_gigs": int(published_gigs),
        "total_orders": int(total_orders),
        "completed_orders": int(completed_orders),
        "revenue_cents": int(revenue),
    }


async def compute_gig_performance(session: AsyncSession) -> list[dict[str, Any]]:
    """Return per-gig order counts.

    Outer joins :class:`Gig` to :class:`Order` and groups by gig so gigs
    without orders are still included with a count of 0.
    """
    result = await session.execute(
        select(
            Gig.id,
            Gig.title,
            func.count(Order.id).label("order_count"),
        )
        .outerjoin(Order, Order.gig_id == Gig.id)
        .group_by(Gig.id, Gig.title)
        .order_by(func.count(Order.id).desc(), Gig.id)
    )
    return [
        {"gig_id": gig_id, "title": title, "order_count": order_count}
        for gig_id, title, order_count in result.all()
    ]


async def analyze_ab_test(session: AsyncSession, gig_id: int) -> dict[str, Any]:
    """Analyze the A/B test for *gig_id*.

    Placeholder: impression/conversion variant tracking is not yet
    implemented, so this returns an indeterminate result with a note
    explaining that variant tracking needs implementation.
    """
    gig = await session.get(Gig, gig_id)
    if gig is None:
        return {
            "gig_id": gig_id,
            "winner": None,
            "confidence": 0.0,
            "note": "Gig not found",
        }

    variants = gig.ab_variants_json or {}
    if not variants:
        return {
            "gig_id": gig_id,
            "winner": None,
            "confidence": 0.0,
            "note": (
                "Variant tracking needs implementation: "
                "no A/B variants recorded for this gig"
            ),
        }

    return {
        "gig_id": gig_id,
        "winner": None,
        "confidence": 0.0,
        "note": (
            "Variant tracking needs implementation: "
            "impression/conversion metrics not yet recorded"
        ),
    }
