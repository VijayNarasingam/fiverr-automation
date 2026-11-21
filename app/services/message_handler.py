"""Auto-reply message handler for the Fiverr agent.

Consumes :class:`app.services.ollama_service.OllamaService` as an LLM fallback.

Functions exposed:
- auto_reply(message_content, gig_context=None) -> str
- should_auto_reply(message_content) -> bool
- COMMON_REPLIES: dict of rule-based replies keyed by keyword
"""

import logging
from typing import Optional

from app.services.ollama_service import OllamaService

logger = logging.getLogger(__name__)

# Spam keywords that should suppress auto-replies.
SPAM_KEYWORDS = ("click here", "win money", "free bitcoin")

# Rule-based replies matched by keyword (case-insensitive substring search).
COMMON_REPLIES = {
    "requirements": (
        "Thanks for reaching out! Could you please share the project "
        "requirements (scope, deliverables, and any reference files) so I can "
        "give you an accurate quote and timeline?"
    ),
    "deadline": (
        "I can usually start right away. What's your deadline? Let me know "
        "when you need the work delivered and I'll confirm if I can meet it."
    ),
    "revision": (
        "Sure thing — revisions are included as described in the gig package. "
        "Please let me know what you'd like changed and I'll get it updated."
    ),
}


def should_auto_reply(message_content: str) -> bool:
    """Return True if *message_content* is eligible for an auto-reply.

    Messages containing spam keywords (``click here``, ``win money``,
    ``free bitcoin``) are filtered out and return False.
    """
    lowered = message_content.lower()
    for keyword in SPAM_KEYWORDS:
        if keyword in lowered:
            logger.info("Message filtered as spam (keyword: %r)", keyword)
            return False
    return True


def _rule_based_reply(message_content: str) -> Optional[str]:
    """Return a COMMON_REPLIES reply if a keyword matches, else None."""
    lowered = message_content.lower()
    for keyword, reply in COMMON_REPLIES.items():
        if keyword in lowered:
            logger.info("Matched rule-based reply for keyword %r", keyword)
            return reply
    return None


async def auto_reply(
    message_content: str,
    gig_context: Optional[dict] = None,
    ollama_service: Optional[OllamaService] = None,
) -> str:
    """Produce an auto-reply for *message_content*.

    Strategy:
      1. Rule-based match against ``COMMON_REPLIES`` keywords.
      2. Fallback to the Ollama LLM (if *ollama_service* is provided and
         reachable), prompted with *gig_context*.
      3. Fallback to a polite generic reply.

    Returns the reply string.
    """
    # 1. Rule-based reply first.
    rule_reply = _rule_based_reply(message_content)
    if rule_reply:
        return rule_reply

    # 2. Ollama LLM fallback.
    ollama = ollama_service or OllamaService()
    try:
        healthy = await ollama.health_check()
    except Exception as exc:  # noqa: BLE001 — treat unreachable as fallback
        logger.warning("Ollama health check failed: %s", exc)
        healthy = False

    if healthy:
        try:
            system_prompt = (
                "You are a polite, professional Fiverr seller replying to a "
                "buyer's message. Keep replies short, friendly, and helpful. "
                "Do not promise anything outside the gig scope."
            )
            context_str = ""
            if gig_context:
                context_str = "\nGig context: " + str(gig_context)
            user_prompt = (
                "Buyer message:\n"
                f"{message_content}"
                f"{context_str}\n"
                "Write a short reply."
            )
            reply = await ollama.generate(
                [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.5,
                max_tokens=250,
            )
            if reply and reply.strip():
                return reply.strip()
        except Exception as exc:  # noqa: BLE001 — fall back to generic
            logger.warning("Ollama reply generation failed: %s", exc)

    # 3. Generic fallback.
    return (
        "Thanks for your message! I'll get back to you shortly with more "
        "details. In the meantime, feel free to share any additional "
        "requirements."
    )


async def process_new_messages() -> list:
    """Process inbound messages that have not been auto-replied yet.

    For each inbound message with ``is_auto_replied`` False, generate a reply
    via :func:`auto_reply` (when :func:`should_auto_reply` allows it),
    persist an outbound :class:`Message` and mark the original as auto-replied.

    Returns the list of :class:`Message` instances that were processed.
    """
    from sqlalchemy import select

    from app.database import async_session
    from app.models.message import Message, MessageDirection

    processed: list[Message] = []

    async with async_session() as db_session:
        stmt = (
            select(Message)
            .where(Message.direction == MessageDirection.INBOUND)
            .where(Message.is_auto_replied.is_(False))
        )
        result = await db_session.execute(stmt)
        messages = result.scalars().all()

        for message in messages:
            if not should_auto_reply(message.content):
                # Not eligible for auto-reply; mark as processed so we do not
                # retry it on the next cycle.
                message.is_auto_replied = True
                continue

            reply = await auto_reply(message.content)
            outbound = Message(
                order_id=message.order_id,
                direction=MessageDirection.OUTBOUND,
                content=reply,
                is_auto_replied=True,
            )
            db_session.add(outbound)
            message.is_auto_replied = True
            processed.append(message)

        await db_session.commit()

    logger.info("Processed %d new messages", len(processed))
    return processed
