"""Tests for the Fiverr gig publisher.

All browser interactions are mocked so no real browser is launched and no
network requests are made.
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


def _make_mock_page(logged_in=True, gig_url="https://www.fiverr.com/seller/gig/abc123"):
    """Build a mock Page whose selectors resolve as if logged in and published."""
    page = AsyncMock()

    def query_selector_side_effect(selector):
        mock_el = MagicMock()
        # Title field present => logged in.
        if 'input[name="title"]' in selector or 'input[id^="gig-title"]' in selector:
            return mock_el if logged_in else None
        # Description textarea present.
        if "textarea" in selector or 'role="textbox"' in selector:
            return mock_el
        # Category select present.
        if "select" in selector or "combobox" in selector:
            return mock_el
        # Package fields present.
        if any(k in selector for k in ("_price", "_days", "_revisions")):
            return mock_el
        # Tag input present.
        if "tags" in selector:
            return mock_el
        # Add FAQ button present.
        if "Add FAQ" in selector:
            return mock_el
        # FAQ inputs present.
        if "faq_question" in selector or "faq_answer" in selector:
            return mock_el
        # File input present.
        if 'input[type="file"]' in selector:
            return mock_el
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
async def test_publish_gig_success_path(mocker, async_session):
    """Happy path: logged in, form filled, publishes to a gig URL."""
    gig = _make_gig()
    async_session.add(gig)
    await async_session.commit()

    mock_page = _make_mock_page(logged_in=True)
    mock_context = AsyncMock()
    mock_browser = AsyncMock()
    mock_browser.new_context = AsyncMock(return_value=mock_context)
    mock_browser.new_page = AsyncMock(return_value=mock_page)

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
    assert result["gig_id"] == "abc123"
    assert result["gig_url"] == "https://www.fiverr.com/seller/gig/abc123"
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
    assert gig.gig_id == "abc123"
    assert gig.gig_url == "https://www.fiverr.com/seller/gig/abc123"
    assert gig.error_message is None

    # Sheets updated.
    mock_sheets.update_gig_status.assert_called_once()
    args, kwargs = mock_sheets.update_gig_status.call_args
    assert args[1] == "published"
    assert kwargs["gig_id"] == "abc123"
    assert kwargs["gig_url"] == "https://www.fiverr.com/seller/gig/abc123"


@pytest.mark.asyncio
async def test_publish_gig_login_flow(mocker, async_session):
    """Not logged in: login form filled, session saved, then form filled."""
    gig = _make_gig()
    async_session.add(gig)
    await async_session.commit()

    # First query_selector (logged-in check) returns None => not logged in.
    # Subsequent calls return truthy elements.
    call_state = {"logged_in_checked": False}

    def query_selector_side_effect(selector):
        if 'input[name="title"]' in selector or 'input[id^="gig-title"]' in selector:
            if not call_state["logged_in_checked"]:
                call_state["logged_in_checked"] = True
                return None  # not logged in on first check
            return MagicMock()  # logged in after login
        return MagicMock()

    mock_page = AsyncMock()
    mock_page.query_selector = AsyncMock(side_effect=query_selector_side_effect)
    mock_page.wait_for_selector = AsyncMock()
    mock_page.fill = AsyncMock()
    mock_page.click = AsyncMock()
    mock_page.select_option = AsyncMock()
    mock_page.set_input_files = AsyncMock()
    mock_page.keyboard.press = AsyncMock()
    mock_page.goto = AsyncMock()
    mock_page.wait_for_load_state = AsyncMock()
    mock_page.wait_for_url = AsyncMock()
    mock_page.url = "https://www.fiverr.com/seller/gig/xyz789"

    mock_context = AsyncMock()
    mock_browser = AsyncMock()
    mock_browser.new_context = AsyncMock(return_value=mock_context)
    mock_browser.new_page = AsyncMock(return_value=mock_page)

    mock_content_engine = AsyncMock()
    mock_content_engine.enhance_gig_content = AsyncMock(
        return_value={
            "title": "I will write a python script",
            "description": "Enhanced description",
            "faq_json": [],
            "tags": ["python"],
            "ab_variants": [],
        }
    )
    mock_sheets = MagicMock()
    mock_sheets.update_gig_status = MagicMock(return_value={"replies": []})

    with patch.object(gig_publisher, "BrowserService", return_value=mock_browser), patch.object(
        gig_publisher, "ContentEngine", return_value=mock_content_engine
    ), patch.object(gig_publisher, "SheetsService", return_value=mock_sheets), _patch_db_session(
        async_session
    ):
        result = await gig_publisher.publish_gig(gig)

    assert result["success"] is True
    assert result["gig_id"] == "xyz789"

    # Session saved after login.
    mock_context.close.assert_awaited_once()
    mock_browser.stop.assert_awaited_once()

    await async_session.refresh(gig)
    assert gig.status == GigStatus.PUBLISHED


@pytest.mark.asyncio
async def test_publish_gig_failure_path(mocker, async_session):
    """Exception during publish: status FAILED, error_message set, cleanup runs."""
    gig = _make_gig()
    async_session.add(gig)
    await async_session.commit()

    mock_page = AsyncMock()
    mock_page.query_selector = AsyncMock(return_value=MagicMock())  # logged in
    mock_page.wait_for_selector = AsyncMock()
    mock_page.fill = AsyncMock(side_effect=RuntimeError("selectors not found"))
    mock_page.click = AsyncMock()
    mock_page.goto = AsyncMock()
    mock_page.wait_for_url = AsyncMock()
    mock_page.url = "https://www.fiverr.com/sell/gigs/create"

    mock_context = AsyncMock()
    mock_browser = AsyncMock()
    mock_browser.new_context = AsyncMock(return_value=mock_context)
    mock_browser.new_page = AsyncMock(return_value=mock_page)

    mock_content_engine = AsyncMock()
    mock_content_engine.enhance_gig_content = AsyncMock(
        return_value={"title": "t", "description": "d", "faq_json": [], "tags": [], "ab_variants": []}
    )
    mock_sheets = MagicMock()
    mock_sheets.update_gig_status = MagicMock(return_value={"replies": []})

    with patch.object(gig_publisher, "BrowserService", return_value=mock_browser), patch.object(
        gig_publisher, "ContentEngine", return_value=mock_content_engine
    ), patch.object(gig_publisher, "SheetsService", return_value=mock_sheets), _patch_db_session(
        async_session
    ):
        result = await gig_publisher.publish_gig(gig)

    assert result["success"] is False
    assert "selectors not found" in result["error"]

    await async_session.refresh(gig)
    assert gig.status == GigStatus.FAILED
    assert gig.error_message == "selectors not found"

    # Sheets updated with failure status.
    mock_sheets.update_gig_status.assert_any_call(
        gig.id - 1, GigStatus.FAILED.value, error_message="selectors not found"
    )

    # Cleanup still ran.
    mock_context.close.assert_awaited_once()
    mock_browser.stop.assert_awaited_once()


@pytest.mark.asyncio
async def test_human_delay_sleeps_random(mocker):
    """human_delay calls asyncio.sleep with a value in the given range."""
    sleep_mock = mocker.patch("app.services.gig_publisher.asyncio.sleep", new=AsyncMock())
    await gig_publisher.human_delay(0.5, 1.5)
    sleep_mock.assert_awaited_once()
    dur = sleep_mock.await_args.args[0]
    assert 0.5 <= dur <= 1.5


def test_safe_fill_and_safe_click_are_coroutines():
    """safe_fill / safe_click exist as async helpers (importable)."""
    import asyncio

    assert asyncio.iscoroutinefunction(gig_publisher.safe_fill)
    assert asyncio.iscoroutinefunction(gig_publisher.safe_click)
