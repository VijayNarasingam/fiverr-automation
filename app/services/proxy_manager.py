"""Proxy management for the browser automation service.

Consumes :class:`app.config.Settings` (``PROXY_API_URLS``) and provides proxy
fetching, validation, and round-robin rotation. No real network calls are made
during tests — ``httpx`` is mocked.
"""

import logging
from typing import List

import httpx

from app.config import settings

logger = logging.getLogger(__name__)


class ProxyManager:
    """Fetch, validate, and rotate proxies from the configured proxy API URLs."""

    def __init__(self, proxy_api_urls: str | None = None):
        self.proxy_api_urls = proxy_api_urls or settings.PROXY_API_URLS
        self._proxies: List[str] = []
        self._index: int = 0

    def _parse_urls(self) -> List[str]:
        """Split the comma-separated PROXY_API_URLS into a list of URLs."""
        return [url.strip() for url in self.proxy_api_urls.split(",") if url.strip()]

    async def fetch_proxies(self) -> List[str]:
        """Fetch proxy strings from the configured API URLs."""
        proxies: List[str] = []
        async with httpx.AsyncClient(timeout=10.0) as client:
            for url in self._parse_urls():
                try:
                    response = await client.get(url)
                    response.raise_for_status()
                    for line in response.text.splitlines():
                        line = line.strip()
                        if line:
                            proxies.append(line)
                except httpx.HTTPError as exc:
                    logger.warning("Failed to fetch proxies from %s: %s", url, exc)
        self._proxies = proxies
        self._index = 0
        return self._proxies

    async def validate_proxy(self, proxy: str) -> bool:
        """Validate a proxy by hitting example.com through it using httpx."""
        proxy_url = proxy if "://" in proxy else f"http://{proxy}"
        try:
            async with httpx.AsyncClient(proxies=proxy_url, timeout=10.0) as client:
                response = await client.get("https://example.com", timeout=10.0)
                return response.status_code == 200
        except httpx.HTTPError:
            return False

    async def get_valid_proxies(self) -> List[str]:
        """Fetch proxies and return only the ones that validate."""
        proxies = await self.fetch_proxies()
        valid: List[str] = []
        for proxy in proxies:
            if await self.validate_proxy(proxy):
                valid.append(proxy)
        self._proxies = valid
        self._index = 0
        return valid

    def next_proxy(self) -> str:
        """Return the next proxy in round-robin order, or an empty string if none."""
        if not self._proxies:
            return ""
        proxy = self._proxies[self._index]
        self._index = (self._index + 1) % len(self._proxies)
        return proxy
