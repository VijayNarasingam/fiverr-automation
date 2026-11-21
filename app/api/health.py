"""Health endpoint for the Fiverr Automation Agent API.

Consumes :class:`app.services.ollama_service.OllamaService`.
Produces: GET /api/health returning API status and Ollama health.
"""

from fastapi import APIRouter

from app.services.ollama_service import OllamaService

router = APIRouter(prefix="/api")


@router.get("/health")
async def health():
    """Return the API status together with Ollama reachability."""
    ollama = OllamaService()
    ollama_ok = await ollama.health_check()
    return {
        "status": "ok" if ollama_ok else "degraded",
        "ollama": ollama_ok,
    }
