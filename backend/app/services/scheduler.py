"""Background scheduler for periodic RSS feed refreshing."""

import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.config import settings
from app.services.feed import refresh_all_feeds

logger = logging.getLogger("omnitube.scheduler")

scheduler = AsyncIOScheduler()


def start_scheduler():
    """Start the background RSS polling scheduler."""
    scheduler.add_job(
        refresh_all_feeds,
        "interval",
        minutes=settings.rss_poll_interval,
        id="rss_poll",
        replace_existing=True,
        max_instances=1,
    )
    scheduler.start()
    logger.info(f"Scheduler started: polling every {settings.rss_poll_interval} minutes")


def stop_scheduler():
    """Shut down the scheduler gracefully."""
    if scheduler.running:
        scheduler.shutdown(wait=False)
        logger.info("Scheduler stopped")
