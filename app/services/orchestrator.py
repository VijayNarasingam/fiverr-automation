"""Orchestrator for the Fiverr automation cycles.

Consumes :func:`app.services.gig_publisher.publish_gig`,
:func:`app.services.order_manager.sync_orders`,
:func:`app.services.message_handler.process_new_messages`, the
:class:`app.models.gig.Gig` model and
:class:`app.services.sheets_service.SheetsService`.

Produces:
- :meth:`run_gig_creation_cycle` -> ``{processed, succeeded, failed, errors}``
- :meth:`run_order_sync_cycle` -> ``{synced: count}``
- :meth:`run_message_cycle` -> ``{messages_processed: count}``
"""

import asyncio
import logging
from typing import Any

from app.config import settings
from app.database import async_session
from app.models.gig import Gig, GigStatus
from app.services.gig_publisher import publish_gig
from app.services.message_handler import process_new_messages
from app.services.order_manager import sync_orders
from app.services.sheets_service import SheetsService

logger = logging.getLogger(__name__)

# Delay (seconds) between publishing gigs to respect Fiverr rate limits.
GIG_DELAY_SECONDS = 300

# Sheet statuses that mean a gig still needs to be created/published.
_PENDING_STATUSES = {"pending", "draft", ""}


class Orchestrator:
    """Coordinates the gig creation, order sync and inbound message cycles."""

    def __init__(self, sheets_service: SheetsService | None = None):
        self.sheets_service = sheets_service or SheetsService()

    # ------------------------------------------------------------------ #
    # Gig creation cycle
    # ------------------------------------------------------------------ #
    async def run_gig_creation_cycle(self) -> dict[str, Any]:
        """Read pending gigs from Sheets, publish each one, track results.

        Respects ``settings.MAX_GIGS_PER_RUN`` and inserts a
        ``GIG_DELAY_SECONDS`` delay between gigs for rate limiting.

        Returns a dict with the keys ``processed``, ``succeeded``, ``failed``
        and ``errors``.
        """
        processed = 0
        succeeded = 0
        failed = 0
        errors: list[str] = []

        rows = self._read_pending_gig_rows()
        limit = settings.MAX_GIGS_PER_RUN

        for index, row in enumerate(rows):
            if processed >= limit:
                break

            gig = self._row_to_gig(row, index)
            if gig is None:
                continue

            # Persist the Gig row before attempting to publish it.
            async with async_session() as db_session:
                db_session.add(gig)
                await db_session.commit()
                await db_session.refresh(gig)

            processed += 1

            try:
                result = await publish_gig(gig)

                if result.get("success"):
                    succeeded += 1
                    logger.info("Gig %s published successfully", gig.id)
                else:
                    failed += 1
                    error = result.get("error") or "unknown error"
                    errors.append(error)
                    logger.warning("Gig %s failed to publish: %s", gig.id, error)

            except Exception as exc:  # noqa: BLE001 — never abort the whole cycle
                logger.exception("Failed to process gig row %s", index)
                failed += 1
                errors.append(str(exc))

            # Rate-limit: delay between gigs, but not after the last one.
            has_more = (index + 1) < len(rows) and processed < limit
            if has_more:
                await asyncio.sleep(GIG_DELAY_SECONDS)

        return {
            "processed": processed,
            "succeeded": succeeded,
            "failed": failed,
            "errors": errors,
        }

    # ------------------------------------------------------------------ #
    # Order sync cycle
    # ------------------------------------------------------------------ #
    async def run_order_sync_cycle(self) -> dict[str, Any]:
        """Synchronize orders from Fiverr into the database.

        Returns ``{synced: count}``.
        """
        synced = await sync_orders()
        return {"synced": len(synced)}

    # ------------------------------------------------------------------ #
    # Message cycle
    # ------------------------------------------------------------------ #
    async def run_message_cycle(self) -> dict[str, Any]:
        """Process new inbound messages and auto-reply where appropriate.

        Returns ``{messages_processed: count}``.
        """
        processed = await process_new_messages()
        count = len(processed) if isinstance(processed, list) else int(processed or 0)
        return {"messages_processed": count}

    # ------------------------------------------------------------------ #
    # Helpers
    # ------------------------------------------------------------------ #
    def _read_pending_gig_rows(self) -> list[dict]:
        """Return sheet rows whose gig has not yet been published or failed."""
        rows = self.sheets_service.read_gig_rows()
        pending = []
        for row in rows:
            status = (row.get("Status") or row.get("status") or "").strip().lower()
            if status in _PENDING_STATUSES:
                pending.append(row)
        return pending

    @staticmethod
    def _to_int(value, default: int = 0) -> int:
        try:
            return int(value)
        except (TypeError, ValueError):
            return default

    @staticmethod
    def _parse_list(value) -> list:
        if value is None:
            return []
        if isinstance(value, list):
            return value
        if isinstance(value, str):
            return [v.strip() for v in value.split(",") if v.strip()]
        return [value]

    def _row_to_gig(self, row: dict, row_index: int) -> Gig | None:
        """Map a sheet row to a :class:`Gig`, returning None if unusable."""
        title = (row.get("Title") or row.get("title") or "").strip()
        if not title:
            return None

        price = self._to_int(row.get("Price") or row.get("price"))
        days = self._to_int(row.get("Days") or row.get("days"), default=3)
        revisions = self._to_int(row.get("Revisions") or row.get("revisions"))
        features = self._parse_list(row.get("Features") or row.get("features"))
        tags = row.get("Tags") or row.get("tags") or ""
        description = row.get("Description") or row.get("description") or ""

        gig = Gig(
            category=row.get("Category") or row.get("category") or "General",
            subcategory=row.get("Subcategory") or row.get("subcategory") or "",
            title_template=title,
            description_template=description,
            title=title,
            description=description,
            package_basic_price=price,
            package_basic_days=days,
            package_basic_revisions=revisions,
            package_basic_features=features,
            package_standard_price=price * 2,
            package_standard_days=days,
            package_standard_revisions=revisions + 1,
            package_standard_features=list(features),
            package_premium_price=price * 3,
            package_premium_days=days,
            package_premium_revisions=revisions + 2,
            package_premium_features=list(features),
            extras_json=[],
            faq_json=[],
            requirements_json=[],
            tags=tags,
            ab_variants_json={},
            status=GigStatus.PENDING,
        )
        # Stash the originating sheet row so publish_gig can update Sheets.
        gig._sheet_row_index = row_index
        return gig
