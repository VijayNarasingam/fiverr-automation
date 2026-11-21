"""End-to-end test for the gig publish flow.

Verifies gig publish -> database updated to PUBLISHED -> Google Sheets updated,
with all external dependencies (browser, content engine, sheets) mocked so no
real browser, network, or Fiverr access is used.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.models.gig import Gig, GigStatus
from app.services import gig_publisher


def _make_gig(**overrides):
    defaults = dict(
        id=1,
        category="Programming & Tech",
        subcategory="Python",
        title_template="I will write a {task} python script",
        description_template="Custom python script for {task}",
        title="I will write a python script",
        description="A custom python script",
        package_basic_price=10,
        package_basic_days=3,
        package_basic_revisions=2,
        package_basic_features=["Feature A"],
        package_standard_price=25,
        package_standard_days=2,
        package_standard_revisions=3,
        package_standard_features=["Feature A", "Feature B"],
        package_premium_price=50,
        package_premium_days=1,
        package_premium_revisions=5,
        package_premium_features=["Feature A", "Feature B", "Feature C"],
        extras_json=[],
        faq_json=[],
        requirements_json=[],
        image_urls="",
        tags="python, script",
        ab_variants_json={},
        status=GigStatus.DRAFT,
        gig_id=None,
        gig_url=None,
        error_message=None,
    )
    defaults.update(overrides)
    return Gig(**defaults)


class _AsyncSessionContextManager:
    """Async context manager that yields a given AsyncSession."""

    def __init__(self, session):
        self.session = session

    async def __aenter__(self):
        return self.session

    async def __aexit__(self, exc_type, exc, tb):
        return False


def _patch_db_session(session):
    """Patch ``gig_publisher.async_session`` so _update_db_gig uses *session*."""
    cm = _AsyncSessionContextManager(session)
    return patch.object(gig_publisher, "async_session", MagicMock(return_value=cm))


def _make_mock_page(logged_in=True, gig_url="https://www.fiverr.com/seller/gig/e2e-abc123"):
    """Build a mock Page whose selectors resolve as if logged in and published."""
    page = AsyncMock()

    def query_selector_side_effect(selector):
        mock_el = MagicMock()
        if 'input[name="title"]' in selector or 'input[id^="gig-title"]' in selector:
            return mock_el if logged_in else None
        return mock_el

    page.query_selector = AsyncMock(side_effect=query_selector_side_effect)
    page.wait_for_selector = AsyncMock()
    page.fill = AsyncMock()
    page.click = AsyncMock()
    page.select_option = AsyncMock()
    page.set_input_files = AsyncMock()
    page.keyboard.press = AsyncMock()
    page.goto = AsyncMock()
    page.wait_for_load_state = AsyncMock()
    page.wait_for_url = AsyncMock()
    page.url = gig_url
    return page


@pytest.mark.asyncio
async def test_e2e_gig_publish_flow(async_session):
    """E2E: publish_gig end-to-end with mocked browser/content/sheets.

    Asserts success=True, gig_id captured from the published URL, the database
    row updated to PUBLISHED (gig_id/gig_url set, error cleared) and Google
    Sheets updated with the published status.
    """
    gig = _make_gig()
    async_session.add(gig)
    await async_session.commit()

    mock_page = _make_mock_page(logged_in=True)
    mock_context = AsyncMock()
    mock_browser = AsyncMock()
    mock_browser.start = AsyncMock()
    mock_browser.new_context = AsyncMock(return_value=mock_context)
    mock_browser.new_page = AsyncMock(return_value=mock_page)
    mock_browser.load_session = AsyncMock()
    mock_browser.save_session = AsyncMock()
    mock_browser.stop = AsyncMock()

    # Mock the content engine.
    enhanced = {
        "title": "I will write a python script",
        "description": "Enhanced python script description",
        "faq_json": [{"question": "Q?", "answer": "A."}],
        "tags": ["python", "script"],
        "ab_variants": [],
    }
    mock_content_engine = AsyncMock()
    mock_content_engine.enhance_gig_content = AsyncMock(return_value=enhanced)

    # Mock sheets service.
    mock_sheets = MagicMock()
    mock_sheets.update_gig_status = MagicMock(return_value={"replies": []})

    with patch.object(gig_publisher, "BrowserService", return_value=mock_browser), patch.object(
        gig_publisher, "ContentEngine", return_value=mock_content_engine
    ), patch.object(gig_publisher, "SheetsService", return_value=mock_sheets), _patch_db_session(
        async_session
    ):
        result = await gig_publisher.publish_gig(gig)

    assert result["success"] is True
    assert result["gig_id"] == "e2e-abc123"
    assert result["gig_url"] == "https://www.fiverr.com/seller/gig/e2e-abc123"
    assert result["error"] is None

    # Browser lifecycle methods called.
    mock_browser.start.assert_awaited_once()
    mock_browser.new_context.assert_awaited_once()
    mock_browser.new_page.assert_awaited_once()
    mock_context.close.assert_awaited_once()
    mock_browser.stop.assert_awaited_once()

    # Navigated to the create-gig URL.
    mock_page.goto.assert_awaited_once()
    assert "fiverr.com/sell/gigs/create" in mock_page.goto.await_args.args[0]

    # Content engine enhanced content.
    mock_content_engine.enhance_gig_content.assert_awaited_once()

    # Database updated to PUBLISHED.
    await async_session.refresh(gig)
    assert gig.status == GigStatus.PUBLISHED
    assert gig.gig_id == "e2e-abc123"
    assert gig.gig_url == "https://www.fiverr.com/seller/gig/e2e-abc123"
    assert gig.error_message is None

    # Sheets updated.
    mock_sheets.update_gig_status.assert_called_once()
    args, kwargs = mock_sheets.update_gig_status.call_args
    assert args[1] == "published"
    assert kwargs["gig_id"] == "e2e-abc123"
    assert kwargs["gig_url"] == "https://www.fiverr.com/seller/gig/e2e-abc123"
