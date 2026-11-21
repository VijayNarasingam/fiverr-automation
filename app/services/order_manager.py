"""Order synchronization and status management for the Fiverr agent.

Consumes :class:`app.services.browser_service.BrowserService` and the
:class:`app.models.gig.Gig` / :class:`app.models.order.Order` models.

Functions exposed:
- sync_orders(gig_id=None) -> list[Order]
- update_order_status(order_id, new_status)
"""

import logging
from typing import Optional

from sqlalchemy import select

from app.database import async_session
from app.models.gig import Gig, GigStatus
from app.models.order import Order, OrderStatus

logger = logging.getLogger(__name__)

# Fiverr orders page URL.
FIVERR_ORDERS_URL = "https://www.fiverr.com/orders"

# CSS selectors used to locate order rows/cells on the Fiverr orders page.
# These are best-effort and may need adjustment as Fiverr's markup changes.
ORDER_ROW_SELECTOR = "div.order-row, tr.order-row, [data-testid*='order']"
ORDER_ID_SELECTOR = "[data-order-id], .order-id"
BUYER_SELECTOR = ".buyer-username, [data-buyer]"
AMOUNT_SELECTOR = ".order-amount, [data-amount]"
STATUS_SELECTOR = ".order-status, [data-status]"
DEADLINE_SELECTOR = ".order-deadline, [data-deadline]"


async def _load_browser():
    """Lazily construct a :class:`BrowserService` instance."""
    from app.services.browser_service import BrowserService

    return BrowserService(headless=True)


async def _parse_orders_from_page(page):
    """Parse order records from a loaded Fiverr orders page.

    Returns a list of dicts with keys: fiverr_order_id, buyer_username,
    amount, status, deadline. Real navigation/DOM parsing is intentionally
    stubbed out here -- callers that need live Fiverr data should wire this
    up against actual page selectors. For now we return an empty list so the
    sync structure exists without hitting Fiverr.
    """
    # NOTE: Real Fiverr navigation is skipped per the task requirements.
    # The structure below is the placeholder where DOM parsing would live.
    return []


async def sync_orders(gig_id: Optional[int] = None) -> list:
    """Synchronize orders from Fiverr into the database.

    Queries published gigs (optionally filtered by *gig_id*), navigates to
    the Fiverr orders page for each gig that has a ``gig_id``, parses order
    data and creates :class:`Order` records for orders not already present.

    Because real Fiverr navigation is skipped, this currently returns an
    empty list but establishes the full database/structural flow.
    """
    synced: list = []

    async with async_session() as db_session:
        stmt = select(Gig).where(Gig.status == GigStatus.PUBLISHED)
        if gig_id is not None:
            stmt = stmt.where(Gig.id == gig_id)
        result = await db_session.execute(stmt)
        gigs = result.scalars().all()

        for gig in gigs:
            if not gig.gig_id:
                logger.info(
                    "Skipping sync for gig %s: no Fiverr gig_id set", gig.id
                )
                continue

            # Real browser navigation to the Fiverr orders page would happen
            # here. Skipped per task requirements; parse returns [].
            try:
                orders_data = await _parse_orders_from_page(None)
            except Exception as exc:  # noqa: BLE001 — never abort the whole sync
                logger.exception("Failed to parse orders for gig %s: %s", gig.id, exc)
                continue

            for order_data in orders_data:
                existing = await db_session.execute(
                    select(Order).where(
                        Order.fiverr_order_id == order_data["fiverr_order_id"]
                    )
                )
                if existing.scalar() is not None:
                    continue
                order = Order(
                    gig_id=gig.id,
                    fiverr_order_id=order_data["fiverr_order_id"],
                    buyer_username=order_data.get("buyer_username", ""),
                    amount=order_data.get("amount", 0),
                    status=OrderStatus(
                        order_data.get("status", OrderStatus.NEW.value)
                    ),
                    deadline=order_data.get("deadline"),
                    requirements=order_data.get("requirements", {}),
                )
                db_session.add(order)
                synced.append(order)

        await db_session.commit()

    logger.info("Synced %d orders", len(synced))
    return synced


async def update_order_status(order_id: int, new_status) -> bool:
    """Load an :class:`Order` by id, update its status and commit.

    Returns True if the order was found and updated, False otherwise.
    *new_status* may be an :class:`OrderStatus` enum or its string value.
    """
    from app.models.order import OrderStatus as _OrderStatus

    if isinstance(new_status, str):
        try:
            new_status = _OrderStatus(new_status)
        except ValueError:
            logger.warning("Invalid order status %r", new_status)
            return False

    async with async_session() as db_session:
        order = await db_session.get(Order, order_id)
        if order is None:
            logger.warning("Order %s not found; cannot update status", order_id)
            return False
        order.status = new_status
        await db_session.commit()
        logger.info("Updated order %s status to %s", order_id, new_status.value)
        return True
