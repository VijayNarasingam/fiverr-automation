"""End-to-end test for the order flow.

Verifies order status transition NEW -> IN_PROGRESS using the async_session
fixture, with all external dependencies mocked so no real browser, network,
or Fiverr access is used.
"""

from unittest.mock import MagicMock, patch

import pytest

from app.models.gig import Gig, GigStatus
from app.models.order import Order, OrderStatus
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
async def test_e2e_order_status_transition_new_to_in_progress(async_session):
    """E2E: create Order NEW, transition to IN_PROGRESS, assert status changed."""
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
        gig_id="e2e-gig-1",
        gig_url="https://www.fiverr.com/seller/gig/e2e-gig-1",
    )
    async_session.add(gig)
    await async_session.commit()

    order = Order(
        gig_id=gig.id,
        fiverr_order_id="E2E-ORDER-1",
        buyer_username="buyer1",
        amount=1500,
        status=OrderStatus.NEW,
    )
    async_session.add(order)
    await async_session.commit()

    assert order.status == OrderStatus.NEW

    with _patch_db_session(async_session):
        updated = await order_manager.update_order_status(order.id, OrderStatus.IN_PROGRESS)
    assert updated is True

    await async_session.refresh(order)
    assert order.status == OrderStatus.IN_PROGRESS
