"""Tests for the NVIDIA LLM service.

All ``httpx`` calls are mocked so no real LLM calls are made.
"""

from unittest.mock import AsyncMock, MagicMock

import httpx
import pytest

from app.config import settings
from app.services.llm_service import LLMService

CHAT_COMPLETION_PAYLOAD = {
    "choices": [{"message": {"content": "This is the generated response."}}]
}


def _make_client(payload: dict = CHAT_COMPLETION_PAYLOAD):
    """Build an httpx AsyncClient mock that returns *payload* as JSON."""

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json = MagicMock(return_value=payload)
    mock_response.raise_for_status = MagicMock()

    mock_client = AsyncMock()
    mock_client.post = AsyncMock(return_value=mock_response)
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)
    return mock_client


@pytest.mark.asyncio
async def test_generate_posts_chat_completions_and_returns_content(mocker):
    mock_client = _make_client()
    mocker.patch(
        "app.services.llm_service.httpx.AsyncClient", return_value=mock_client
    )

    llm = LLMService(
        base_url="https://integrate.api.nvidia.com/v1",
        api_key="test-key",
        model="nemotron-3.5-super-vl-120b-a12b",
    )
    messages = [
        {"role": "system", "content": "You are a copywriter."},
        {"role": "user", "content": "Write a gig description."},
    ]
    content = await llm.generate(messages, temperature=0.7, max_tokens=512)

    assert content == "This is the generated response."
    mock_client.post.assert_called_once()
    call_args = mock_client.post.call_args
    assert call_args[0][0] == "https://integrate.api.nvidia.com/v1/chat/completions"
    json_payload = call_args[1]["json"]
    assert json_payload["model"] == "nemotron-3.5-super-vl-120b-a12b"
    assert json_payload["messages"] == messages
    assert json_payload["temperature"] == 0.7
    assert json_payload["max_tokens"] == 512
    assert json_payload["stream"] is False
    # Check Authorization header
    headers = call_args[1]["headers"]
    assert headers.get("Authorization") == "Bearer test-key"


@pytest.mark.asyncio
async def test_generate_uses_default_model_and_settings_url(mocker):
    mock_client = _make_client()
    mocker.patch(
        "app.services.llm_service.httpx.AsyncClient", return_value=mock_client
    )

    llm = LLMService()
    await llm.generate([{"role": "user", "content": "Hello"}])

    json_payload = mock_client.post.call_args[1]["json"]
    assert json_payload["model"] == settings.NVIDIA_MODEL
    assert mock_client.post.call_args[0][0].endswith("/chat/completions")


@pytest.mark.asyncio
async def test_generate_raises_on_http_error(mocker):
    mock_response = MagicMock()
    mock_response.status_code = 500
    mock_response.raise_for_status = MagicMock(
        side_effect=httpx.HTTPStatusError(
            "server error", request=MagicMock(), response=mock_response
        )
    )

    mock_client = AsyncMock()
    mock_client.post = AsyncMock(return_value=mock_response)
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)
    mocker.patch(
        "app.services.llm_service.httpx.AsyncClient", return_value=mock_client
    )

    llm = LLMService()
    with pytest.raises(httpx.HTTPStatusError):
        await llm.generate([{"role": "user", "content": "Hello"}])


@pytest.mark.asyncio
async def test_health_check_true(mocker):
    mock_client = _make_client()
    mocker.patch(
        "app.services.llm_service.httpx.AsyncClient", return_value=mock_client
    )

    llm = LLMService()
    assert await llm.health_check() is True


@pytest.mark.asyncio
async def test_health_check_false(mocker):
    mock_client = AsyncMock()
    mock_client.post = AsyncMock(side_effect=httpx.HTTPError("connection refused"))
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)
    mocker.patch(
        "app.services.llm_service.httpx.AsyncClient", return_value=mock_client
    )

    llm = LLMService()
    assert await llm.health_check() is False