"""Tests for proxy validation.

All ``httpx`` calls are mocked so no real network requests are made.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from app.services.proxy_manager import ProxyManager


def _make_validation_client(status_code: int | None = None):
    """Build an httpx AsyncClient mock whose .get returns a given status code."""

    mock_response = MagicMock()
    mock_response.status_code = status_code

    mock_client = AsyncMock()
    mock_client.get = AsyncMock(return_value=mock_response)
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)
    return mock_client


@pytest.mark.asyncio
async def test_validate_proxy_success():
    """A proxy returning HTTP 200 validates as valid."""
    mock_client = _make_validation_client(200)

    with patch(
        "app.services.proxy_manager.httpx.AsyncClient", return_value=mock_client
    ):
        pm = ProxyManager()
        assert await pm.validate_proxy("1.1.1.1:8080") is True

    mock_client.get.assert_called_once_with("https://example.com", timeout=10.0)


@pytest.mark.asyncio
async def test_validate_proxy_failure():
    """A proxy that raises httpx.HTTPError validates as invalid."""
    mock_client = AsyncMock()
    mock_client.get = AsyncMock(side_effect=httpx.HTTPError("connection refused"))
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)

    with patch(
        "app.services.proxy_manager.httpx.AsyncClient", return_value=mock_client
    ):
        pm = ProxyManager()
        assert await pm.validate_proxy("1.1.1.1:8080") is False
