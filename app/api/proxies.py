"""Proxy status and validation endpoints.

Consumes :class:`app.services.proxy_manager.ProxyManager`.
Produces: GET /api/proxies, POST /api/proxies/validate.
"""

from typing import Any

from fastapi import APIRouter

from app.services.proxy_manager import ProxyManager

router = APIRouter(prefix="/api/proxies")

proxy_manager = ProxyManager()


@router.get("")
async def get_proxies() -> dict[str, Any]:
    """Return proxy rotation status: total valid proxies and current index."""
    return {
        "total": len(proxy_manager._proxies),
        "current_index": proxy_manager._index,
    }


@router.post("/validate")
async def validate_proxies() -> dict[str, Any]:
    """Fetch proxies from the configured API URLs and return the valid count."""
    valid = await proxy_manager.get_valid_proxies()
    return {"valid_count": len(valid)}
