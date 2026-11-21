"""NVIDIA API endpoints for LLM content generation.

Provides REST endpoints to interact with the NVIDIA Nemotron model:
- GET /api/nvidia/health — check NVIDIA API reachability
- POST /api/nvidia/generate — generate chat completion
- GET /api/nvidia/settings — get current NVIDIA configuration (API key masked)
"""

from typing import Any

from fastapi import APIRouter, HTTPException

from app.config import settings
from app.services.llm_service import LLMService

router = APIRouter(prefix="/api/nvidia")


@router.get("/health")
async def nvidia_health() -> dict[str, Any]:
    """Return NVIDIA API reachability status."""
    llm = LLMService()
    ok = await llm.health_check()
    return {
        "status": "ok" if ok else "degraded",
        "nvidia": ok,
        "model": settings.NVIDIA_MODEL,
        "base_url": settings.NVIDIA_BASE_URL,
    }


@router.post("/generate")
async def nvidia_generate(payload: dict[str, Any]) -> dict[str, Any]:
    """Generate a chat completion via NVIDIA Nemotron.

    Body:
        messages: list of {role, content} dicts
        temperature: float (default 0.7)
        max_tokens: int (default 512)
    """
    messages = payload.get("messages")
    if not messages or not isinstance(messages, list):
        raise HTTPException(status_code=400, detail="messages is required")

    temperature = payload.get("temperature", 0.7)
    max_tokens = payload.get("max_tokens", 512)

    llm = LLMService()
    try:
        content = await llm.generate(
            messages,  # type: ignore[arg-type]
            temperature=float(temperature),
            max_tokens=int(max_tokens),
        )
        return {"content": content, "model": settings.NVIDIA_MODEL}
    except Exception as exc:  # noqa: BLE001 — surface LLM errors as HTTP 502
        raise HTTPException(
            status_code=502, detail=f"NVIDIA generation failed: {exc}"
        )


@router.get("/settings")
async def nvidia_settings() -> dict[str, Any]:
    """Return current NVIDIA configuration (API key masked)."""
    api_key = settings.NVIDIA_API_KEY
    return {
        "nvidia_base_url": settings.NVIDIA_BASE_URL,
        "nvidia_model": settings.NVIDIA_MODEL,
        "nvidia_api_key_configured": bool(api_key),
        "nvidia_api_key_masked": "***" if api_key else "",
    }