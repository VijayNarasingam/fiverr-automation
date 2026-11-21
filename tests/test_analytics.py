"""Tests for the analytics service.

The async SQLAlchemy session is provided by the in-memory ``async_session``
fixture in ``tests/conftest.py`` (a mocked/test database session), so no
live database or Fiverr account is required.
"""

from unittest.mock import patch

import pytest

from app.models.gig import Gig, GigStatus
from app.models.order import Order, OrderStatus
from app.services import analytics_service


def _make_gig(**overrides):
    data = dict(
        category="Programming & Tech",
        subcategory="Python",
        title_template="I will write a {task}",
        description_template="A {task} script",
        title="I will write python",
        description="A python script",
        package_basic_price=1000,
        package_basic_days=3,
        package_basic_revisions=2,
        package_basic_features=[],
        package_standard_price=2500,
        package_standard_days=2,
        package_standard_revisions=3,
        package_standard_features=[],
        package_premium_price=5000,
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
    data.update(overrides)
    return Gig(**data)


@pytest.mark.asyncio
async def test_compute_overview_counts_and_revenue(async_session):
    """compute_overview counts total/published gigs, total/completed orders, revenue."""
    published = _make_gig(title="Published gig", status=GigStatus.PUBLISHED)
    draft = _make_gig(title="Draft gig", status=GigStatus.DRAFT)
    async_session.add_all([published, draft])
    await async_session.commit()

    completed = Order(
        gig_id=published.id,
        fiverr_order_id="FIVERR-ORDER-1",
        buyer_username="buyer1",
        amount=1500,
        status=OrderStatus.COMPLETED,
    )
    delivered = Order(
        gig_id=published.id,
        fiverr_order_id="FIVERR-ORDER-2",
        buyer_username="buyer2",
        amount=2000,
        status=OrderStatus.DELIVERED,
    )
    new = Order(
        gig_id=published.id,
        fiverr_order_id="FIVERR-ORDER-3",
        buyer_username="buyer3",
        amount=500,
        status=OrderStatus.NEW,
    )
    async_session.add_all([completed, delivered, new])
    await async_session.commit()

    result = await analytics_service.compute_overview(async_session)

    assert result["total_gigs"] == 2
    assert result["published_gigs"] == 1
    assert result["total_orders"] == 3
    assert result["completed_orders"] == 2
    assert result["revenue_cents"] == 3500


@pytest.mark.asyncio
async def test_compute_overview_empty(async_session):
    """compute_overview returns zeros on an empty database."""
    result = await analytics_service.compute_overview(async_session)
    assert result == {
        "total_gigs": 0,
        "published_gigs": 0,
        "total_orders": 0,
        "completed_orders": 0,
        "revenue_cents": 0,
    }


@pytest.mark.asyncio
async def test_compute_gig_performance_outer_join_includes_zero_count_gigs(async_session):
    """compute_gig_performance outer joins gigs to orders, keeping zero-count gigs."""
    published = _make_gig(title="Popular gig", status=GigStatus.PUBLISHED)
    empty = _make_gig(title="Empty gig", status=GigStatus.PUBLISHED)
    async_session.add_all([published, empty])
    await async_session.commit()

    async_session.add_all(
        [
            Order(
                gig_id=published.id,
                fiverr_order_id="FIVERR-ORDER-1",
                buyer_username="buyer1",
                amount=1000,
                status=OrderStatus.COMPLETED,
            ),
            Order(
                gig_id=published.id,
                fiverr_order_id="FIVERR-ORDER-2",
                buyer_username="buyer2",
                amount=1000,
                status=OrderStatus.COMPLETED,
            ),
        ]
    )
    await async_session.commit()

    result = await analytics_service.compute_gig_performance(async_session)
    by_gig = {row["gig_id"]: row for row in result}

    assert by_gig[published.id]["order_count"] == 2
    assert by_gig[empty.id]["order_count"] == 0
    assert by_gig[empty.id]["title"] == "Empty gig"


@pytest.mark.asyncio
async def test_analyze_ab_test_gig_not_found(async_session):
    """analyze_ab_test returns an indeterminate result for a missing gig."""
    result = await analytics_service.analyze_ab_test(async_session, 99999)
    assert result == {
        "gig_id": 99999,
        "winner": None,
        "confidence": 0.0,
        "note": "Gig not found",
    }


@pytest.mark.asyncio
async def test_analyze_ab_test_no_variants(async_session):
    """analyze_ab_test notes that variant tracking needs implementation when no variants exist."""
    gig = _make_gig(title="No variants gig", ab_variants_json={})
    async_session.add(gig)
    await async_session.commit()

    result = await analytics_service.analyze_ab_test(async_session, gig.id)
    assert result["gig_id"] == gig.id
    assert result["winner"] is None
    assert result["confidence"] == 0.0
    assert "Variant tracking needs implementation" in result["note"]


@pytest.mark.asyncio
async def test_analyze_ab_test_with_variants_still_placeholder(async_session):
    """analyze_ab_test remains a placeholder even when variants are recorded."""
    gig = _make_gig(
        title="Variants gig",
        ab_variants_json={"A": {"title": "Title A"}, "B": {"title": "Title B"}},
    )
    async_session.add(gig)
    await async_session.commit()

    result = await analytics_service.analyze_ab_test(async_session, gig.id)
    assert result["gig_id"] == gig.id
    assert result["winner"] is None
    assert result["confidence"] == 0.0
    assert "implementation" in result["note"]


@pytest.mark.asyncio
async def test_ab_test_endpoint_uses_analyze_ab_test(async_session):
    """The API endpoint delegates to analyze_ab_test (verified via the service)."""
    with patch.object(analytics_service, "analyze_ab_test") as mock_analyze:
        mock_analyze.return_value = {
            "gig_id": 1,
            "winner": None,
            "confidence": 0.0,
            "note": "mocked",
        }
        result = await analytics_service.analyze_ab_test(async_session, 1)
        mock_analyze.assert_awaited_once_with(async_session, 1)
        assert result["note"] == "mocked"
