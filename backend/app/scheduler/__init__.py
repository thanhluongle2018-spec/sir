from __future__ import annotations

import logging
from datetime import datetime, timezone

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.config import get_settings
from app.db import SessionLocal
from app.services.monitor import tick_due_tasks

logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler(timezone="UTC")


async def _job_tick() -> None:
    db = SessionLocal()
    try:
        ran = await tick_due_tasks(db)
        if ran:
            logger.info("scheduler tick ran %s tasks at %s", ran, datetime.now(timezone.utc).isoformat())
    finally:
        db.close()


def start_scheduler() -> None:
    settings = get_settings()
    if not settings.scheduler_enabled:
        logger.info("scheduler disabled")
        return
    if scheduler.running:
        return
    scheduler.add_job(
        _job_tick,
        "interval",
        seconds=5,
        id="monitor_tick",
        replace_existing=True,
        max_instances=1,
        coalesce=True,
    )
    scheduler.start()
    logger.info("scheduler started")


def stop_scheduler() -> None:
    if scheduler.running:
        scheduler.shutdown(wait=False)
        logger.info("scheduler stopped")
