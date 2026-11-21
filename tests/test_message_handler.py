"""Tests for the message handler.

NVIDIA LLM service is mocked so no real LLM calls are made.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services import message_handler


def _make_mock_llm(reply_content="This is an LLM-generated reply."):
    """Build an LLMService mock whose generate() returns *reply_content*."""
    mock_llm = AsyncMock()
    mock_llm.health_check = AsyncMock(return_value=True)
    mock_llm.generate = AsyncMock(return_value=reply_content)
    return mock_llm


@pytest.mark.asyncio
async def test_auto_reply_rule_based_requirements():
    """Messages containing 'requirements' get the rule-based reply."""
    reply = await message_handler.auto_reply(
        "What are the requirements for this gig?"
    )
    assert "requirements" in reply.lower()
    assert "scope" in reply.lower()


@pytest.mark.asyncio
async def test_auto_reply_rule_based_deadline():
    """Messages containing 'deadline' get the rule-based reply."""
    reply = await message_handler.auto_reply("What is your deadline?")
    assert "deadline" in reply.lower()


@pytest.mark.asyncio
async def test_auto_reply_rule_based_revision():
    """Messages containing 'revision' get the rule-based reply."""
    reply = await message_handler.auto_reply("Can I request a revision?")
    assert "revision" in reply.lower()


@pytest.mark.asyncio
async def test_auto_reply_uses_llm_fallback(mocker):
    """When no rule matches, fall back to NVIDIA LLM."""
    mock_llm = _make_mock_llm("LLM says hello.")
    reply = await message_handler.auto_reply(
        "Something completely unrelated to keywords.",
        llm_service=mock_llm,
    )
    assert reply == "LLM says hello."
    mock_llm.generate.assert_awaited_once()


@pytest.mark.asyncio
async def test_auto_reply_llm_unreachable_uses_generic(mocker):
    """When NVIDIA is unreachable, fall back to a generic reply."""
    mock_llm = _make_mock_llm("unused")
    mock_llm.health_check = AsyncMock(return_value=False)
    reply = await message_handler.auto_reply(
        "Something unrelated.", llm_service=mock_llm
    )
    assert "Thanks for your message" in reply


@pytest.mark.asyncio
async def test_auto_reply_llm_exception_uses_generic(mocker):
    """When NVIDIA raises, fall back to a generic reply."""
    mock_llm = AsyncMock()
    mock_llm.health_check = AsyncMock(side_effect=RuntimeError("down"))
    reply = await message_handler.auto_reply(
        "Something unrelated.", llm_service=mock_llm
    )
    assert "Thanks for your message" in reply


def test_should_auto_reply_filters_spam():
    """Spam keywords suppress auto-replies."""
    assert message_handler.should_auto_reply("click here to win") is False
    assert message_handler.should_auto_reply("win money now") is False
    assert message_handler.should_auto_reply("free bitcoin giveaway") is False


def test_should_auto_reply_allows_legitimate():
    """Legitimate messages are eligible for auto-replies."""
    assert message_handler.should_auto_reply("Hello, what are your rates?") is True
    assert message_handler.should_auto_reply("Can you do this by Friday?") is True


def test_common_replies_has_expected_keys():
    """COMMON_REPLIES contains requirements, deadline and revision."""
    assert "requirements" in message_handler.COMMON_REPLIES
    assert "deadline" in message_handler.COMMON_REPLIES
    assert "revision" in message_handler.COMMON_REPLIES
    for key, reply in message_handler.COMMON_REPLIES.items():
        assert isinstance(reply, str) and reply.strip()