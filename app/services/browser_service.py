"""Browser automation service for the Fiverr agent.

Launches a headless Chromium browser via Playwright, creates browser contexts
with optional proxy support, applies stealth to pages, and persists/restores
session cookies to the database ``Session`` model.
"""

import json
import logging
from typing import Optional

from playwright.async_api import Browser, BrowserContext, Page, async_playwright

from app.config import settings
from app.database import async_session
from app.models.session import Session
from app.services.proxy_manager import ProxyManager
from app.services.stealth_manager import apply_stealth

logger = logging.getLogger(__name__)

SESSION_ID = "fiverr_main"


class BrowserService:
    """Wrapper around Playwright for browser automation with stealth and sessions."""

    def __init__(self, headless: bool = True, proxy_manager: Optional[ProxyManager] = None):
        self.headless = headless
        self.proxy_manager = proxy_manager or ProxyManager()
        self._playwright = None
        self._browser: Optional[Browser] = None
        self._context: Optional[BrowserContext] = None

    async def start(self) -> Browser:
        """Launch Chromium headless and store the browser instance."""
        self._playwright = await async_playwright().start()
        launch_options = {"headless": self.headless}
        proxy = self.proxy_manager.next_proxy()
        if proxy:
            launch_options["proxy"] = {"server": proxy}
            logger.info("Launching browser with proxy %s", proxy)
        self._browser = await self._playwright.chromium.launch(**launch_options)
        return self._browser

    async def stop(self) -> None:
        """Close the browser and shut down Playwright."""
        if self._browser:
            await self._browser.close()
            self._browser = None
        if self._playwright:
            await self._playwright.stop()
            self._playwright = None

    async def new_context(self, proxy: Optional[str] = None) -> BrowserContext:
        """Create a new browser context, optionally with a proxy."""
        if not self._browser:
            await self.start()
        context_options: dict = {}
        if proxy:
            context_options["proxy"] = {"server": proxy}
        self._context = await self._browser.new_context(**context_options)
        return self._context

    async def new_page(self) -> Page:
        """Create a new page in the current context with stealth applied."""
        if not self._context:
            await self.new_context()
        page = await self._context.new_page()
        await apply_stealth(page)
        return page

    async def load_session(self, context: BrowserContext, session_id: str = SESSION_ID) -> None:
        """Load cookies from the database into the given browser context."""
        async with async_session() as db_session:
            result = await db_session.get(Session, session_id)
            if result and result.cookies_json:
                cookies = json.loads(result.cookies_json)
                await context.add_cookies(cookies)
                logger.info("Loaded session %s with %d cookies", session_id, len(cookies))

    async def save_session(self, context: BrowserContext, session_id: str = SESSION_ID) -> None:
        """Save the browser context cookies to the database."""
        cookies = await context.cookies()
        cookies_json = json.dumps(cookies)
        async with async_session() as db_session:
            db_session_obj = await db_session.get(Session, session_id)
            if db_session_obj is None:
                db_session_obj = Session(id=session_id, cookies_json=cookies_json)
                db_session.add(db_session_obj)
            else:
                db_session_obj.cookies_json = cookies_json
            await db_session.commit()
        logger.info("Saved session %s with %d cookies", session_id, len(cookies))

    @property
    def browser(self) -> Optional[Browser]:
        return self._browser

    @property
    def context(self) -> Optional[BrowserContext]:
        return self._context


async def launch_browser(headless: bool = True) -> BrowserService:
    """Convenience function to create and start a BrowserService."""
    service = BrowserService(headless=headless)
    await service.start()
    return service
