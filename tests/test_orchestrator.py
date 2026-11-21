"""Tests for the Fiverr automation orchestrator.

All external dependencies (Sheets, publish_gig, sync_orders,
process_new_messages, the database session and asyncio.sleep) are mocked so no
real network, browser, scheduler or Google Sheets calls are made. The scheduler
is never started — only job registration is verified.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services import orchestrator
from app.services.orchestrator import Orchestrator
from app.services.proxy_manager import ProxyManager
from app.services.scheduler import build_scheduler


def _make_sheet_row(
    title="I will write a python script", status="pending", **overrides
):
    row = {
        "Title": title,
        "Category": "Programming & Tech",
        "Subcategory": "Python",
        "Description": "A custom python script",
        "Price": "10",
        "Days": "3",
        "Revisions": "2",
        "Tags": "python, script",
        "Status": status,
    }
    row.update(overrides)
    return row


class _AsyncSessionContextManager:
    """Async context manager that yields a given AsyncSession."""

    def __init__(self, session):
        self.session = session

    async def __aenter__(self):
        return self.session

    async def __aexit__(self, exc_type, exc, tb):
        return False


def _patch_db_session(session):
    """Patch ``orchestrator.async_session`` so the orchestrator uses *session*."""
    cm = _AsyncSessionContextManager(session)
    return patch.object(orchestrator, "async_session", MagicMock(return_value=cm))


@pytest.fixture
def mock_sheets():
    sheets = MagicMock()
    sheets.read_gig_rows = MagicMock(return_value=[])
    return sheets


async def test_run_gig_creation_cycle_success(async_session, mock_sheets, mocker):
    """Happy path: two pending gigs both publish successfully."""
    mock_sheets.read_gig_rows = MagicMock(
        return_value=[_make_sheet_row(title="Gig One"), _make_sheet_row(title="Gig Two")]
    )

    publish_results = [
        {
            "success": True,
            "gig_id": "gig1",
            "gig_url": "https://www.fiverr.com/gigs/gig1",
            "error": None,
        },
        {
            "success": True,
            "gig_id": "gig2",
            "gig_url": "https://www.fiverr.com/gigs/gig2",
            "error": None,
        },
    ]
    mock_publish = AsyncMock(side_effect=publish_results)

    # Never actually sleep 300s between gigs in tests.
    mocker.patch("app.services.orchestrator.GIG_DELAY_SECONDS", 0)

    with _patch_db_session(async_session), patch.object(
        orchestrator, "publish_gig", mock_publish
    ):
        result = await Orchestrator(sheets_service=mock_sheets).run_gig_creation_cycle()

    assert result == {
        "processed": 2,
        "succeeded": 2,
        "failed": 0,
        "errors": [],
    }
    assert mock_publish.await_count == 2


async def test_run_gig_creation_cycle_respects_max_gigs(
    async_session, mock_sheets, mocker
):
    """The cycle stops after MAX_GIGS_PER_RUN gigs."""
    mock_sheets.read_gig_rows = MagicMock(
        return_value=[
            _make_sheet_row(title="Gig One"),
            _make_sheet_row(title="Gig Two"),
            _make_sheet_row(title="Gig Three"),
        ]
    )
    mock_publish = AsyncMock(
        return_value={
            "success": True,
            "gig_id": "g1",
            "gig_url": "https://www.fiverr.com/gigs/g1",
            "error": None,
        }
    )
    mocker.patch("app.services.orchestrator.GIG_DELAY_SECONDS", 0)

    with _patch_db_session(async_session), patch.object(
        orchestrator, "publish_gig", mock_publish
    ):
        result = await Orchestrator(sheets_service=mock_sheets).run_gig_creation_cycle()

    assert result["processed"] == 2
    assert result["succeeded"] == 2
    assert result["failed"] == 0
    assert result["errors"] == []
    assert mock_publish.await_count == 2


async def test_run_gig_creation_cycle_failure(async_session, mock_sheets, mocker):
    """A publish failure increments failed and records the error."""
    mock_sheets.read_gig_rows = MagicMock(
        return_value=[_make_sheet_row(title="Gig One")]
    )
    mock_publish = AsyncMock(
        return_value={
            "success": False,
            "gig_id": None,
            "gig_url": None,
            "error": "boom",
        }
    )
    mocker.patch("app.services.orchestrator.GIG_DELAY_SECONDS", 0)

    with _patch_db_session(async_session), patch.object(
        orchestrator, "publish_gig", mock_publish
    ):
        result = await Orchestrator(sheets_service=mock_sheets).run_gig_creation_cycle()

    assert result == {
        "processed": 1,
        "succeeded": 0,
        "failed": 1,
        "errors": ["boom"],
    }


async def test_run_gig_creation_cycle_empty_sheet(mock_sheets, mocker):
    """No pending rows => nothing processed and no publish calls."""
    mock_sheets.read_gig_rows = MagicMock(return_value=[])
    mock_publish = AsyncMock()
    mocker.patch("app.services.orchestrator.GIG_DELAY_SECONDS", 0)

    with patch.object(orchestrator, "publish_gig", mock_publish):
        result = await Orchestrator(sheets_service=mock_sheets).run_gig_creation_cycle()

    assert result == {
        "processed": 0,
        "succeeded": 0,
        "failed": 0,
        "errors": [],
    }
    mock_publish.assert_not_awaited()


async def test_run_gig_creation_cycle_skips_non_pending(
    async_session, mock_sheets, mocker
):
    """Rows with status 'published' or 'failed' are skipped."""
    mock_sheets.read_gig_rows = MagicMock(
        return_value=[
            _make_sheet_row(title="Published Gig", status="published"),
            _make_sheet_row(title="Failed Gig", status="failed"),
            _make_sheet_row(title="Pending Gig", status="pending"),
        ]
    )
    mock_publish = AsyncMock(
        return_value={
            "success": True,
            "gig_id": "g1",
            "gig_url": "https://www.fiverr.com/gigs/g1",
            "error": None,
        }
    )
    mocker.patch("app.services.orchestrator.GIG_DELAY_SECONDS", 0)

    with _patch_db_session(async_session), patch.object(
        orchestrator, "publish_gig", mock_publish
    ):
        result = await Orchestrator(sheets_service=mock_sheets).run_gig_creation_cycle()

    assert result == {"processed": 1, "succeeded": 1, "failed": 0, "errors": []}
    assert mock_publish.await_count == 1


async def test_run_order_sync_cycle(async_session, mocker):
    """run_order_sync_cycle delegates to sync_orders and returns the count."""
    mock_sync = AsyncMock(return_value=[MagicMock(), MagicMock()])
    with patch.object(orchestrator, "sync_orders", mock_sync):
        result = await Orchestrator().run_order_sync_cycle()

    assert result == {"synced": 2}
    mock_sync.assert_awaited_once()


async def test_run_message_cycle(async_session, mocker):
    """run_message_cycle delegates to process_new_messages and returns the count."""
    mock_process = AsyncMock(
        return_value=[MagicMock(), MagicMock(), MagicMock()]
    )
    with patch.object(orchestrator, "process_new_messages", mock_process):
        result = await Orchestrator().run_message_cycle()

    assert result == {"messages_processed": 3}
    mock_process.assert_awaited_once()


def test_scheduler_job_registration(mocker):
    """build_scheduler registers the four interval jobs and never starts them."""
    captured = []

    def fake_add_job(func, trigger, **kwargs):
        captured.append({"func": func, "trigger": trigger, "kwargs": kwargs})

    mocker.patch(
        "apscheduler.schedulers.asyncio.AsyncIOScheduler.add_job",
        side_effect=fake_add_job,
    )

    orch = Orchestrator()
    scheduler = build_scheduler(orchestrator=orch)

    assert len(captured) == 4

    ids = [c["kwargs"].get("id") for c in captured]
    assert "gig_creation_cycle" in ids
    assert "order_sync_cycle" in ids
    assert "message_cycle" in ids
    assert "proxy_validation" in ids

    for c in captured:
        assert c["trigger"] == "interval"
        assert c["kwargs"]["max_instances"] == 1
        assert c["kwargs"]["replace_existing"] is True

    minutes = {c["kwargs"]["id"]: c["kwargs"].get("minutes") for c in captured}
    assert minutes["gig_creation_cycle"] == 15
    assert minutes["order_sync_cycle"] == 10
    assert minutes["message_cycle"] == 5

    hours = {c["kwargs"]["id"]: c["kwargs"].get("hours") for c in captured}
    assert hours["proxy_validation"] == 1

    # Each automation job is bound to the supplied orchestrator instance.
    bound = {
        c["kwargs"]["id"]: c["func"] for c in captured
    }
    assert bound["gig_creation_cycle"].__self__ is orch
    assert bound["gig_creation_cycle"].__func__ is Orchestrator.run_gig_creation_cycle
    assert bound["order_sync_cycle"].__self__ is orch
    assert bound["order_sync_cycle"].__func__ is Orchestrator.run_order_sync_cycle
    assert bound["message_cycle"].__self__ is orch
    assert bound["message_cycle"].__func__ is Orchestrator.run_message_cycle
    # Proxy validation is bound to the module-level proxy manager instance.
    assert bound["proxy_validation"].__func__ is ProxyManager.get_valid_proxies

    # Scheduler was built but not started (start is never invoked here).
    assert scheduler.state == 0  # STATE_STOPPED
