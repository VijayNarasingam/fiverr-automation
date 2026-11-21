"""Tests for the proxy manager.

All ``httpx`` calls are mocked so no real network requests are made.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from app.services.proxy_manager import ProxyManager

PROXY_API_URLS = "https://proxy-api.example.com/list"


def _make_client(get_response):
    """Build a factory returning a fresh httpx AsyncClient mock per call."""

    def factory(*args, **kwargs):
        mock_response = MagicMock()
        mock_response.status_code = get_response.get("status_code", 200)
        mock_response.text = get_response.get("text", "")
        mock_response.raise_for_status = MagicMock()

        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        return mock_client

    return factory


@pytest.mark.asyncio
async def test_fetch_proxies_splits_comma_separated_urls():
    # One client is reused for all URLs, so .get must differentiate by URL.
    async def get_side_effect(url, **kwargs):
        if url == "https://a.example.com":
            text = "1.1.1.1:8080\n"
        else:
            text = "2.2.2.2:3128\n"
        response = MagicMock()
        response.status_code = 200
        response.text = text
        response.raise_for_status = MagicMock()
        return response

    mock_client = AsyncMock()
    mock_client.get = AsyncMock(side_effect=get_side_effect)
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)

    with patch(
        "app.services.proxy_manager.httpx.AsyncClient", return_value=mock_client
    ):
        pm = ProxyManager(proxy_api_urls="https://a.example.com,https://b.example.com")
        proxies = await pm.fetch_proxies()

    assert proxies == ["1.1.1.1:8080", "2.2.2.2:3128"]


@pytest.mark.asyncio
async def test_fetch_proxies_handles_empty_response():
    with patch(
        "app.services.proxy_manager.httpx.AsyncClient",
        side_effect=_make_client({"text": ""}),
    ):
        pm = ProxyManager(proxy_api_urls=PROXY_API_URLS)
        proxies = await pm.fetch_proxies()

    assert proxies == []


@pytest.mark.asyncio
async def test_fetch_proxies_skips_failed_url():
    async def get_side_effect(url, **kwargs):
        if "fail" in url:
            raise httpx.HTTPError("boom")
        response = MagicMock()
        response.status_code = 200
        response.text = "3.3.3.3:8080"
        response.raise_for_status = MagicMock()
        return response

    mock_client = AsyncMock()
    mock_client.get = AsyncMock(side_effect=get_side_effect)
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)

    with patch(
        "app.services.proxy_manager.httpx.AsyncClient", return_value=mock_client
    ):
        pm = ProxyManager(proxy_api_urls="https://fail.example.com,https://ok.example.com")
        proxies = await pm.fetch_proxies()

    assert proxies == ["3.3.3.3:8080"]


@pytest.mark.asyncio
async def test_validate_proxy_true(mocker):
    mock_response = MagicMock()
    mock_response.status_code = 200

    mock_client = AsyncMock()
    mock_client.get = AsyncMock(return_value=mock_response)
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)

    mocker.patch("app.services.proxy_manager.httpx.AsyncClient", return_value=mock_client)

    pm = ProxyManager()
    assert await pm.validate_proxy("1.1.1.1:8080") is True
    mock_client.get.assert_called_once_with("https://example.com", timeout=10.0)


@pytest.mark.asyncio
async def test_validate_proxy_false(mocker):
    mock_client = AsyncMock()
    mock_client.get = AsyncMock(side_effect=httpx.HTTPError("connection refused"))
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)

    mocker.patch("app.services.proxy_manager.httpx.AsyncClient", return_value=mock_client)

    pm = ProxyManager()
    assert await pm.validate_proxy("1.1.1.1:8080") is False


@pytest.mark.asyncio
async def test_next_proxy_round_robin():
    pm = ProxyManager()
    pm._proxies = ["a:8080", "b:8080", "c:8080"]
    assert pm.next_proxy() == "a:8080"
    assert pm.next_proxy() == "b:8080"
    assert pm.next_proxy() == "c:8080"
    assert pm.next_proxy() == "a:8080"  # wraps around


def test_next_proxy_empty_returns_empty_string():
    pm = ProxyManager()
    assert pm.next_proxy() == ""
