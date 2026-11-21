"""Fiverr gig publisher using Playwright automation.

Consumes :class:`app.services.browser_service.BrowserService`,
:class:`app.services.content_engine.ContentEngine`, the :class:`app.models.gig.Gig`
model and :class:`app.services.sheets_service.SheetsService` to fill out and
submit the Fiverr "create a gig" form, then persists the result back to the
database and Google Sheets.
"""

import asyncio
import logging
import random
import re
from typing import Any

from playwright.async_api import Page

from app.config import settings
from app.database import async_session
from app.models.gig import Gig, GigStatus
from app.services.browser_service import BrowserService
from app.services.content_engine import ContentEngine
from app.services.sheets_service import SheetsService

logger = logging.getLogger(__name__)

FIVERR_CREATE_GIG_URL = "https://www.fiverr.com/sell/gigs/create"

# A published gig URL looks like https://www.fiverr.com/<username>/gig/<id> or
# https://www.fiverr.com/gigs/<id>. Match both shapes.
GIG_URL_PATTERN = re.compile(r"https?://[^/]+/(?:[^/]+/)?gigs?/[^/?#]+")

GIG_ID_URL_PATTERN = re.compile(r"/gigs?/([^/?#]+)")


async def human_delay(min_seconds: float = 0.5, max_seconds: float = 1.5) -> None:
    """Sleep for a random duration to mimic human interaction timing."""
    await asyncio.sleep(random.uniform(min_seconds, max_seconds))


async def safe_fill(page: Page, selector: str, value: str, timeout: int = 5000) -> None:
    """Wait for *selector* to appear then fill *value* into it."""
    await page.wait_for_selector(selector, state="visible", timeout=timeout)
    await page.fill(selector, value)
    logger.debug("Filled %s with %r", selector, value)


async def safe_click(page: Page, selector: str, timeout: int = 5000) -> None:
    """Wait for *selector* to appear then click it."""
    await page.wait_for_selector(selector, state="visible", timeout=timeout)
    await page.click(selector)
    logger.debug("Clicked %s", selector)


async def publish_gig(gig: Gig) -> dict[str, Any]:
    """Publish a single :class:`Gig` to Fiverr.

    Returns a dict with the keys ``success``, ``gig_id``, ``gig_url`` and
    ``error``. On success the database row is updated (``status`` = PUBLISHED,
    ``gig_id``, ``gig_url``) and Google Sheets is updated via
    :meth:`SheetsService.update_gig_status`. On failure ``status`` is set to
    FAILED with ``error_message`` populated and the browser/context are still
    cleaned up in the ``finally`` block.
    """
    browser_service = BrowserService(headless=settings.HEADLESS if hasattr(settings, "HEADLESS") else True)
    content_engine = ContentEngine()
    sheets_service = SheetsService()

    context = None
    page = None
    result: dict[str, Any] = {
        "success": False,
        "gig_id": None,
        "gig_url": None,
        "error": None,
    }

    try:
        await browser_service.start()
        context = await browser_service.new_context(use_proxy=True)
        await browser_service.load_session(context)
        page = await browser_service.new_page()

        await page.goto(FIVERR_CREATE_GIG_URL, wait_until="domcontentloaded")
        await human_delay()

        # Determine whether we are already logged in. A logged-in user lands on
        # the gig creation form (look for the title input / "Create a Gig").
        # Otherwise we are redirected to a login page and must authenticate.
        logged_in = await page.query_selector('input[name="title"], input[id^="gig-title"]') is not None

        if not logged_in:
            await _login(page)
            await browser_service.save_session(context)
            # Re-check after login.
            await page.wait_for_load_state("networkidle")
            logged_in = await page.query_selector('input[name="title"], input[id^="gig-title"]') is not None
            if not logged_in:
                raise RuntimeError("Could not reach the gig creation form after login")

        # Enhance the gig content via the content engine (templates + Ollama).
        content = await content_engine.enhance_gig_content(
            {
                "title": gig.title,
                "category": gig.category,
                "price": gig.package_basic_price,
                "description": gig.description,
            }
        )

        await _fill_form(page, gig, content)

        # Submit / publish the gig.
        await safe_click(page, 'button[type="submit"], button:has-text("Publish"), button:has-text("Publish Gig")')
        await human_delay(1.0, 2.0)

        # Wait for the URL to match a published gig URL pattern.
        await page.wait_for_url(GIG_URL_PATTERN, timeout=30000)
        gig_url = page.url
        match = GIG_ID_URL_PATTERN.search(gig_url)
        gig_id = match.group(1) if match else None

        result["success"] = True
        result["gig_id"] = gig_id
        result["gig_url"] = gig_url

        # Persist to the database.
        await _update_db_gig(gig, GigStatus.PUBLISHED, gig_id=gig_id, gig_url=gig_url)

        # Update Google Sheets.
        sheets_service.update_gig_status(
            _row_index_for_gig(gig),
            GigStatus.PUBLISHED.value,
            gig_id=gig_id,
            gig_url=gig_url,
        )

        logger.info("Published gig %s -> %s", gig.id, gig_url)
        return result

    except Exception as exc:  # noqa: BLE001 — surface publish failures gracefully
        logger.exception("Failed to publish gig %s", gig.id)
        result["error"] = str(exc)
        try:
            await _update_db_gig(gig, GigStatus.FAILED, error_message=str(exc))
            sheets_service.update_gig_status(
                _row_index_for_gig(gig),
                GigStatus.FAILED.value,
                error_message=str(exc),
            )
        except Exception:  # noqa: BLE001 — never mask the original error with db/sheets failure
            logger.exception("Failed to record failure for gig %s", gig.id)
        return result

    finally:
        if context is not None:
            try:
                await context.close()
            except Exception:  # noqa: BLE001
                logger.exception("Failed to close browser context")
        await browser_service.stop()


async def _login(page: Page) -> None:
    """Fill the Fiverr login form and submit it."""
    await safe_fill(page, 'input[name="email"], input[type="email"]', settings.FIVERR_EMAIL)
    await safe_fill(page, 'input[name="password"], input[type="password"]', settings.FIVERR_PASSWORD)
    await safe_click(page, 'button[type="submit"], button:has-text("Log in"), button:has-text("Join")')
    await human_delay(1.0, 2.0)


async def _fill_form(page: Page, gig: Gig, content: dict[str, Any]) -> None:
    """Fill every field of the Fiverr gig creation form."""
    # Gig title.
    await safe_fill(page, 'input[name="title"], input[id^="gig-title"]', content.get("title") or gig.title)

    # Category / subcategory (best-effort; Fiverr uses dynamic dropdowns).
    category_selectors = [
        'select[name="category"], select[id^="category"]',
        'div[role="combobox"][aria-label*="Category"]',
    ]
    for selector in category_selectors:
        try:
            await page.wait_for_selector(selector, state="visible", timeout=3000)
            await page.select_option(selector, value=gig.category)
            break
        except Exception:  # noqa: BLE001 — try the next selector
            continue

    # Gig description.
    desc_selectors = [
        'textarea[name="description"], textarea[id^="gig-description"]',
        'div[role="textbox"][aria-label*="Description"]',
    ]
    for selector in desc_selectors:
        try:
            await safe_fill(page, selector, content.get("description") or gig.description)
            break
        except Exception:  # noqa: BLE001
            continue

    # Packages: basic / standard / premium (price, days, revisions).
    for package_name in ("basic", "standard", "premium"):
        price = getattr(gig, f"package_{package_name}_price", None)
        days = getattr(gig, f"package_{package_name}_days", None)
        revisions = getattr(gig, f"package_{package_name}_revisions", None)
        prefix = f'[name="{package_name}_price"], [id^="{package_name}-price"]'
        try:
            await safe_fill(page, prefix, str(price or 0))
        except Exception:  # noqa: BLE001
            logger.debug("Could not fill %s price", package_name)
        days_selector = f'[name="{package_name}_days"], [id^="{package_name}-days"]'
        try:
            await safe_fill(page, days_selector, str(days or 0))
        except Exception:  # noqa: BLE001
            logger.debug("Could not fill %s days", package_name)
        rev_selector = f'[name="{package_name}_revisions"], [id^="{package_name}-revisions"]'
        try:
            await safe_fill(page, rev_selector, str(revisions or 0))
        except Exception:  # noqa: BLE001
            logger.debug("Could not fill %s revisions", package_name)

    # Tags.
    tags = content.get("tags") or gig.tags
    if tags:
        tag_list = [t.strip() for t in tags.split(",")] if isinstance(tags, str) else tags
        for tag in tag_list[:5]:
            try:
                await safe_fill(page, 'input[name="tags"], input[id^="gig-tags"], input[placeholder*="tag"]', tag)
                await page.keyboard.press("Enter")
                await human_delay(0.2, 0.5)
            except Exception:  # noqa: BLE001
                logger.debug("Could not add tag %r", tag)

    # FAQs.
    faqs = content.get("faq_json") or gig.faq_json or []
    for faq in faqs[:5]:
        question = faq.get("question") or faq.get("q", "")
        answer = faq.get("answer") or faq.get("a", "")
        try:
            await safe_click(page, 'button:has-text("Add FAQ"), button[aria-label*="Add FAQ"]')
            await safe_fill(page, 'textarea[name="faq_question"], input[name="faq_question"]', question)
            await safe_fill(page, 'textarea[name="faq_answer"], input[name="faq_answer"]', answer)
        except Exception:  # noqa: BLE001
            logger.debug("Could not add FAQ %r", question)

    # Images.
    image_urls = gig.image_urls or ""
    if image_urls:
        for url in image_urls.split(","):
            url = url.strip()
            if not url:
                continue
            try:
                await safe_click(page, 'button:has-text("Upload"), input[type="file"]')
                await page.set_input_files('input[type="file"]', url)
                await human_delay(0.5, 1.0)
            except Exception:  # noqa: BLE001
                logger.debug("Could not upload image %s", url)


async def _update_db_gig(
    gig: Gig,
    status: GigStatus,
    gig_id: str | None = None,
    gig_url: str | None = None,
    error_message: str | None = None,
) -> None:
    """Persist gig status changes to the database."""
    async with async_session() as db_session:
        db_gig = await db_session.get(Gig, gig.id)
        if db_gig is None:
            logger.warning("Gig %s not found in database; skipping status update", gig.id)
            return
        db_gig.status = status
        if gig_id is not None:
            db_gig.gig_id = gig_id
        if gig_url is not None:
            db_gig.gig_url = gig_url
        if error_message is not None:
            db_gig.error_message = error_message
        if status == GigStatus.PUBLISHED:
            from datetime import datetime, timezone

            db_gig.published_at = datetime.now(timezone.utc)
        await db_session.commit()
        logger.info("Updated gig %s status to %s in database", gig.id, status.value)


def _row_index_for_gig(gig: Gig) -> int:
    """Best-effort mapping of a Gig row to a Google Sheets row_index.

    The caller is expected to store the originating sheet row on the Gig
    instance; fall back to the database primary key minus one (data rows are
    0-based and the first data row is sheet row 2).
    """
    sheet_row = getattr(gig, "_sheet_row_index", None)
    if sheet_row is not None:
        return sheet_row
    return max(0, (gig.id or 1) - 1)
