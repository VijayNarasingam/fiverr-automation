"""Gig endpoints.

Consumes :class:`app.database.get_session`, the :class:`app.models.gig.Gig`
model and :class:`app.services.orchestrator.Orchestrator`.
Produces: GET /api/gigs, POST /api/gigs/publish.
"""

from typing import Any

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.models.gig import Gig
from app.services.orchestrator import Orchestrator

router = APIRouter(prefix="/api")


@router.get("/gigs")
async def list_gigs(
    session: AsyncSession = Depends(get_session),
) -> list[dict[str, Any]]:
    """List every persisted gig."""
    result = await session.execute(select(Gig))
    gigs = result.scalars().all()
    return [
        {
            "id": gig.id,
            "title": gig.title,
            "category": gig.category,
            "status": gig.status,
            "gig_url": gig.gig_url,
        }
        for gig in gigs
    ]


@router.post("/gigs/publish")
async def publish_gigs() -> dict[str, Any]:
    """Trigger a full gig creation cycle via the orchestrator."""
    orchestrator = Orchestrator()
    return await orchestrator.run_gig_creation_cycle()
