"""Tests for the message handler.

Ollama service is mocked so no real LLM calls are made.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services import message_handler


def _make_mock_ollama(reply_content="This is an LLM-generated reply."):
    """Build an OllamaService mock whose generate() returns *reply_content*."""
    mock_ollama = AsyncMock()
    mock_ollama.health_check = AsyncMock(return_value=True)
    mock_ollama.generate = AsyncMock(return_value=reply_content)
    return mock_ollama


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
async def test_auto_reply_uses_ollama_fallback(mocker):
    """When no rule matches, fall back to Ollama LLM."""
    mock_ollama = _make_mock_ollama("LLM says hello.")
    reply = await message_handler.auto_reply(
        "Something completely unrelated to keywords.",
        ollama_service=mock_ollama,
    )
    assert reply == "LLM says hello."
    mock_ollama.generate.assert_awaited_once()


@pytest.mark.asyncio
async def test_auto_reply_ollama_unreachable_uses_generic(mocker):
    """When Ollama is unreachable, fall back to a generic reply."""
    mock_ollama = _make_mock_ollama("unused")
    mock_ollama.health_check = AsyncMock(return_value=False)
    reply = await message_handler.auto_reply(
        "Something unrelated.", ollama_service=mock_ollama
    )
    assert "Thanks for your message" in reply


@pytest.mark.asyncio
async def test_auto_reply_ollama_exception_uses_generic(mocker):
    """When Ollama raises, fall back to a generic reply."""
    mock_ollama = AsyncMock()
    mock_ollama.health_check = AsyncMock(side_effect=RuntimeError("down"))
    reply = await message_handler.auto_reply(
        "Something unrelated.", ollama_service=mock_ollama
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
