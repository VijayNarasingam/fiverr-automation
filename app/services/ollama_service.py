"""Ollama service for LLM-powered gig content generation.

Consumes :class:`app.config.Settings` (``OLLAMA_BASE_URL``) and talks to
Ollama's OpenAI-compatible ``/chat/completions`` endpoint. All HTTP calls go
through ``httpx`` and are mocked in tests — no real LLM calls are made
during testing.
"""

import json
import logging
from typing import Any

import httpx

from app.config import settings

logger = logging.getLogger(__name__)

DEFAULT_MODEL = "hermes3:3b"
CHAT_PATH = "/chat/completions"


class OllamaService:
    """Client for generating and polishing gig content with Ollama."""

    def __init__(self, base_url: str | None = None, model: str = DEFAULT_MODEL):
        self.base_url = (base_url or settings.OLLAMA_BASE_URL).rstrip("/")
        self.model = model

    def _chat_url(self) -> str:
        return f"{self.base_url}{CHAT_PATH}"

    async def generate(
        self,
        messages: list[dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 512,
    ) -> str:
        """POST a chat completion and return the assistant's message content.

        Sends ``model``, ``messages``, ``temperature``, ``max_tokens`` and
        ``stream=False`` to ``{base_url}/chat/completions``.
        """
        payload: dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": False,
        }
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(self._chat_url(), json=payload)
            response.raise_for_status()
        data = response.json()
        return data["choices"][0]["message"]["content"]

    async def polish_description(self, description: str) -> str:
        """Rewrite *description* as compelling, scannable Fiverr gig copy."""
        system_prompt = (
            "You are an expert Fiverr copywriter. Rewrite the following gig "
            "description to be persuasive, scannable, and conversion-focused. "
            "Keep it professional, use short paragraphs and bullet points, and "
            "include a clear call to action. Return only the rewritten "
            "description."
        )
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": description},
        ]
        return await self.generate(messages, temperature=0.7, max_tokens=900)

    async def generate_faq(self, row: dict) -> list[dict[str, str]]:
        """Generate 5 FAQ question/answer pairs for a gig, parsed from JSON."""
        title = row.get("title", row.get("Gig Title", ""))
        category = row.get("category", row.get("Category", ""))
        system_prompt = (
            "You are an expert Fiverr copywriter. Generate exactly 5 frequently "
            "asked questions and answers for the gig described below. Return "
            "ONLY a valid JSON array of objects with keys \"question\" and "
            "\"answer\", nothing else."
        )
        user_prompt = (
            f"Gig title: {title}\n"
            f"Category: {category}\n"
            f"Description: {row.get('description', row.get('Description', ''))}\n"
        )
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]
        content = await self.generate(messages, temperature=0.5, max_tokens=900)
        try:
            faq = json.loads(content)
            if isinstance(faq, list):
                return [
                    {
                        "question": str(item.get("question", "")),
                        "answer": str(item.get("answer", "")),
                    }
                    for item in faq
                    if isinstance(item, dict)
                ][:5]
        except (json.JSONDecodeError, TypeError, AttributeError) as exc:
            logger.warning("Failed to parse FAQ JSON from Ollama: %s", exc)
        return []

    async def suggest_tags(self, row: dict) -> list[str]:
        """Suggest 5 tags for a gig; expects comma-separated output from Ollama."""
        title = row.get("title", row.get("Gig Title", ""))
        category = row.get("category", row.get("Category", ""))
        system_prompt = (
            "You are an expert Fiverr copywriter. Suggest exactly 5 tags "
            "(keywords) for the gig below. Return ONLY a comma-separated list "
            "of tags, nothing else."
        )
        user_prompt = f"Gig title: {title}\nCategory: {category}\n"
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]
        content = await self.generate(messages, temperature=0.5, max_tokens=200)
        tags = [tag.strip() for tag in content.split(",") if tag.strip()]
        return tags[:5]

    async def health_check(self) -> bool:
        """Return True if Ollama is reachable and can generate a completion."""
        try:
            await self.generate(
                [{"role": "user", "content": "Say OK"}],
                temperature=0.0,
                max_tokens=10,
            )
            return True
        except Exception as exc:  # noqa: BLE001 — any failure means unhealthy
            logger.warning("Ollama health check failed: %s", exc)
            return False
