"""Stealth configuration for Playwright pages using playwright-stealth."""

import logging

from playwright.async_api import Page
from playwright_stealth import Stealth

logger = logging.getLogger(__name__)

# Realistic viewport and headers to help avoid bot detection.
VIEWPORT = {"width": 1920, "height": 1080}
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)
HEADERS = {
    "Accept-Language": "en-US,en;q=0.9",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Encoding": "gzip, deflate, br",
    "Upgrade-Insecure-Requests": "1",
}


async def apply_stealth(page: Page) -> None:
    """Apply stealth techniques to a Playwright page.

    Uses playwright-stealth's ``Stealth`` class (``apply_stealth_async``) which
    injects evasion scripts including the ``navigator.webdriver`` mask, then sets
    a realistic viewport and headers.
    """
    await Stealth().apply_stealth_async(page)

    await page.set_viewport_size(VIEWPORT)
    await page.set_extra_http_headers(HEADERS)
    logger.debug("Stealth applied to page")
