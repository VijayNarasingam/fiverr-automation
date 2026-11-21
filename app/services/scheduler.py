"""APScheduler setup for the Fiverr automation cycles.

Registers interval jobs (``max_instances=1`` so cycles never overlap):
- gig creation: every 15 minutes
- order sync: every 10 minutes
- message cycle: every 5 minutes

Call :func:`build_scheduler` to get a configured (but not started)
:class:`~apscheduler.schedulers.asyncio.AsyncIOScheduler`, or
:func:`start_scheduler` to build and start it.
"""

import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.services.orchestrator import Orchestrator

logger = logging.getLogger(__name__)

GIG_CREATION_MINUTES = 15
ORDER_SYNC_MINUTES = 10
MESSAGE_CYCLE_MINUTES = 5


def build_scheduler(orchestrator: Orchestrator | None = None) -> AsyncIOScheduler:
    """Build an :class:`AsyncIOScheduler` with the automation jobs registered.

    The scheduler is returned stopped; call
    :meth:`AsyncIOScheduler.start` to begin running jobs. Jobs are idempotent
    (``replace_existing=True``) so calling this more than once is safe.
    """
    orchestrator = orchestrator or Orchestrator()

    scheduler = AsyncIOScheduler()

    scheduler.add_job(
        orchestrator.run_gig_creation_cycle,
        trigger="interval",
        minutes=GIG_CREATION_MINUTES,
        id="gig_creation_cycle",
        max_instances=1,
        replace_existing=True,
        coalesce=True,
    )
    scheduler.add_job(
        orchestrator.run_order_sync_cycle,
        trigger="interval",
        minutes=ORDER_SYNC_MINUTES,
        id="order_sync_cycle",
        max_instances=1,
        replace_existing=True,
        coalesce=True,
    )
    scheduler.add_job(
        orchestrator.run_message_cycle,
        trigger="interval",
        minutes=MESSAGE_CYCLE_MINUTES,
        id="message_cycle",
        max_instances=1,
        replace_existing=True,
        coalesce=True,
    )

    logger.info(
        "Registered automation jobs: gig_creation=%dmin, order_sync=%dmin, message=%dmin",
        GIG_CREATION_MINUTES,
        ORDER_SYNC_MINUTES,
        MESSAGE_CYCLE_MINUTES,
    )
    return scheduler


def start_scheduler(orchestrator: Orchestrator | None = None) -> AsyncIOScheduler:
    """Build the scheduler and start it running jobs."""
    scheduler = build_scheduler(orchestrator)
    scheduler.start()
    logger.info("Scheduler started")
    return scheduler
