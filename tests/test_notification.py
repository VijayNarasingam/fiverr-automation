"""Tests for the NotificationService.

All ``httpx`` calls are mocked so no real Discord calls are made.
"""

from unittest.mock import AsyncMock, MagicMock

import httpx
import pytest

from app.services.notification_service import NotificationService

WEBHOOK_URL = "https://discord.com/api/webhooks/123/abc"


def _make_client(status_code: int = 200):
    """Build an httpx AsyncClient mock returning *status_code*."""

    mock_response = MagicMock()
    mock_response.status_code = status_code
    mock_response.json = MagicMock(return_value={})
    mock_response.raise_for_status = MagicMock()

    mock_client = AsyncMock()
    mock_client.post = AsyncMock(return_value=mock_response)
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)
    return mock_client


@pytest.mark.asyncio
async def test_send_discord_posts_to_webhook(mocker):
    mock_client = _make_client()
    mocker.patch(
        "app.services.notification_service.httpx.AsyncClient",
        return_value=mock_client,
    )

    service = NotificationService(discord_webhook_url=WEBHOOK_URL)
    assert await service.send_discord("hello world") is True

    mock_client.post.assert_called_once()
    call_args = mock_client.post.call_args
    assert call_args[0][0] == WEBHOOK_URL
    assert call_args[1]["json"] == {"content": "hello world"}


@pytest.mark.asyncio
async def test_send_discord_skipped_when_no_webhook(mocker):
    mock_client = _make_client()
    mocker.patch(
        "app.services.notification_service.httpx.AsyncClient",
        return_value=mock_client,
    )

    service = NotificationService(discord_webhook_url="")
    assert await service.send_discord("hello world") is False
    mock_client.post.assert_not_called()


@pytest.mark.asyncio
async def test_notify_gig_published(mocker):
    mock_client = _make_client()
    mocker.patch(
        "app.services.notification_service.httpx.AsyncClient",
        return_value=mock_client,
    )

    service = NotificationService(discord_webhook_url=WEBHOOK_URL)
    assert await service.notify_gig_published(
        "Logo design", "https://fiverr.com/gig/1"
    ) is True

    payload = mock_client.post.call_args[1]["json"]
    assert payload == {
        "content": "✅ Gig published: Logo design\nhttps://fiverr.com/gig/1"
    }


@pytest.mark.asyncio
async def test_notify_gig_failed(mocker):
    mock_client = _make_client()
    mocker.patch(
        "app.services.notification_service.httpx.AsyncClient",
        return_value=mock_client,
    )

    service = NotificationService(discord_webhook_url=WEBHOOK_URL)
    assert await service.notify_gig_failed("Logo design", "timeout") is True

    payload = mock_client.post.call_args[1]["json"]
    assert payload == {"content": "❌ Gig failed: Logo design\nError: timeout"}


@pytest.mark.asyncio
async def test_notify_new_order(mocker):
    mock_client = _make_client()
    mocker.patch(
        "app.services.notification_service.httpx.AsyncClient",
        return_value=mock_client,
    )

    service = NotificationService(discord_webhook_url=WEBHOOK_URL)
    assert await service.notify_new_order("Logo design", 2500) is True

    payload = mock_client.post.call_args[1]["json"]
    assert payload == {"content": "🔔 New order: Logo design - $25.00"}


@pytest.mark.asyncio
async def test_notify_error(mocker):
    mock_client = _make_client()
    mocker.patch(
        "app.services.notification_service.httpx.AsyncClient",
        return_value=mock_client,
    )

    service = NotificationService(discord_webhook_url=WEBHOOK_URL)
    assert await service.notify_error("SheetError", "row not found") is True

    payload = mock_client.post.call_args[1]["json"]
    assert payload == {"content": "⚠️ SheetError: row not found"}


@pytest.mark.asyncio
async def test_send_discord_http_error_returns_false(mocker):
    mock_response = MagicMock()
    mock_response.status_code = 500
    mock_response.raise_for_status = MagicMock(
        side_effect=httpx.HTTPStatusError(
            "server error", request=MagicMock(), response=mock_response
        )
    )

    mock_client = AsyncMock()
    mock_client.post = AsyncMock(return_value=mock_response)
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)
    mocker.patch(
        "app.services.notification_service.httpx.AsyncClient",
        return_value=mock_client,
    )

    service = NotificationService(discord_webhook_url=WEBHOOK_URL)
    assert await service.send_discord("hello world") is False
