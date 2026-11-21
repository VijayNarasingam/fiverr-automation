"""Notification service for Discord webhook alerts.

Consumes :class:`app.config.Settings` (``DISCORD_WEBHOOK_URL``) and maps
agent events onto the :class:`app.models.audit_log.AuditLog` event
categories (published, failed, new order, error).

Produces: Discord messages sent via httpx POST with ``{"content": message}``.
Only sends when ``DISCORD_WEBHOOK_URL`` is configured.
"""

import logging
from typing import Optional

import httpx

from app.config import settings

logger = logging.getLogger(__name__)


class NotificationService:
    """Send notifications about Fiverr agent events to Discord."""

    def __init__(self, discord_webhook_url: Optional[str] = None) -> None:
        self.discord_webhook_url = discord_webhook_url or settings.DISCORD_WEBHOOK_URL

    async def send_discord(self, message: str) -> bool:
        """POST *message* to the configured Discord webhook URL.

        Returns ``True`` when the message was accepted (or skipped because no
        webhook is configured) and ``False`` on transport/HTTP failure.
        """
        if not self.discord_webhook_url:
            logger.debug("Discord webhook URL not configured; skipping notification")
            return False
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    self.discord_webhook_url,
                    json={"content": message},
                )
                response.raise_for_status()
            logger.info("Discord notification sent successfully")
            return True
        except httpx.HTTPError as exc:
            logger.error("Failed to send Discord notification: %s", exc)
            return False

    async def notify_gig_published(self, title: str, url: str) -> bool:
        """Notify that a gig was published."""
        message = f"✅ Gig published: {title}\n{url}"
        return await self.send_discord(message)

    async def notify_gig_failed(self, title: str, error: str) -> bool:
        """Notify that a gig failed to publish."""
        message = f"❌ Gig failed: {title}\nError: {error}"
        return await self.send_discord(message)

    async def notify_new_order(self, gig_title: str, amount_cents: int) -> bool:
        """Notify that a new order was received."""
        amount = amount_cents / 100
        message = f"🔔 New order: {gig_title} - ${amount:.2f}"
        return await self.send_discord(message)

    async def notify_error(self, error_type: str, details: str) -> bool:
        """Notify that an error occurred."""
        message = f"⚠️ {error_type}: {details}"
        return await self.send_discord(message)
