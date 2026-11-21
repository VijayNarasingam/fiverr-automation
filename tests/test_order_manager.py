"""Tests for the order manager.

Tests that require live Fiverr account access are skipped.
"""

from unittest.mock import MagicMock, patch

import pytest

from app.models.order import OrderStatus
from app.services import order_manager


class _AsyncSessionContextManager:
    """Async context manager that yields a given AsyncSession."""

    def __init__(self, session):
        self.session = session

    async def __aenter__(self):
        return self.session

    async def __aexit__(self, exc_type, exc, tb):
        return False


def _patch_db_session(session):
    """Patch ``order_manager.async_session`` so DB calls use *session*."""
    cm = _AsyncSessionContextManager(session)
    return patch.object(order_manager, "async_session", MagicMock(return_value=cm))


@pytest.mark.asyncio
async def test_sync_orders_returns_list(async_session):
    """sync_orders returns a list (empty when no Fiverr navigation is wired)."""
    with _patch_db_session(async_session):
        orders = await order_manager.sync_orders()
    assert isinstance(orders, list)


@pytest.mark.asyncio
async def test_sync_orders_filters_by_gig_id(async_session):
    """sync_orders accepts an optional gig_id filter without error."""
    with _patch_db_session(async_session):
        orders = await order_manager.sync_orders(gig_id=1)
    assert isinstance(orders, list)


@pytest.mark.skip(reason="Requires Fiverr account access")
@pytest.mark.asyncio
async def test_sync_orders_requires_fiverr_access(async_session):
    """Placeholder test that would hit real Fiverr orders page."""
    orders = await order_manager.sync_orders()
    assert isinstance(orders, list)


@pytest.mark.asyncio
async def test_update_order_status_updates_and_commits(async_session):
    """update_order_status loads an Order, updates status, and commits."""
    from app.models.gig import Gig, GigStatus
    from app.models.order import Order

    gig = Gig(
        category="Programming & Tech",
        subcategory="Python",
        title_template="I will write a {task}",
        description_template="A {task} script",
        title="I will write python",
        description="A python script",
        package_basic_price=10,
        package_basic_days=3,
        package_basic_revisions=2,
        package_basic_features=[],
        package_standard_price=25,
        package_standard_days=2,
        package_standard_revisions=3,
        package_standard_features=[],
        package_premium_price=50,
        package_premium_days=1,
        package_premium_revisions=5,
        package_premium_features=[],
        extras_json=[],
        faq_json=[],
        requirements_json=[],
        image_urls="",
        tags="python",
        ab_variants_json={},
        status=GigStatus.PUBLISHED,
        gig_id=None,
        gig_url=None,
    )
    async_session.add(gig)
    await async_session.commit()

    order = Order(
        gig_id=gig.id,
        fiverr_order_id="FIVERR-ORDER-1",
        buyer_username="buyer1",
        amount=1500,
        status=OrderStatus.NEW,
    )
    async_session.add(order)
    await async_session.commit()

    with _patch_db_session(async_session):
        updated = await order_manager.update_order_status(
            order.id, OrderStatus.IN_PROGRESS
        )
    assert updated is True

    await async_session.refresh(order)
    assert order.status == OrderStatus.IN_PROGRESS

    # Updating a nonexistent order returns False.
    with _patch_db_session(async_session):
        updated = await order_manager.update_order_status(
            99999, OrderStatus.COMPLETED
        )
    assert updated is False
