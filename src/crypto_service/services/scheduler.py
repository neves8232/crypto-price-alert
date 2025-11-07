"""
Background task scheduler for price polling and alert evaluation.
"""

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from datetime import datetime

from crypto_service.config import settings
from crypto_service.database import AsyncSessionLocal
from crypto_service.services.price_collector import PriceCollectorService
from crypto_service.services.alert_engine import AlertEngine
from crypto_service.utils.logging import get_logger

logger = get_logger(__name__)


class BackgroundScheduler:
    """
    Background task scheduler for periodic jobs.
    """

    def __init__(self):
        """Initialize scheduler."""
        self.scheduler = AsyncIOScheduler()
        self._is_running = False

    async def start(self) -> None:
        """Start the scheduler and register jobs."""
        if self._is_running:
            logger.warning("scheduler_already_running")
            return

        logger.info("starting_scheduler")

        # Price polling job
        self.scheduler.add_job(
            self._collect_prices_job,
            trigger=IntervalTrigger(seconds=settings.crypto_poll_interval_seconds),
            id="price_poller",
            name="Cryptocurrency Price Poller",
            max_instances=1,
            replace_existing=True,
        )

        # Alert evaluation job (runs after price updates)
        self.scheduler.add_job(
            self._evaluate_alerts_job,
            trigger=IntervalTrigger(seconds=settings.crypto_poll_interval_seconds),
            id="alert_evaluator",
            name="Alert Evaluator",
            max_instances=1,
            replace_existing=True,
        )

        # Database cleanup job (daily)
        self.scheduler.add_job(
            self._cleanup_old_data_job,
            trigger=IntervalTrigger(hours=24),
            id="db_cleanup",
            name="Database Cleanup",
            max_instances=1,
            replace_existing=True,
        )

        self.scheduler.start()
        self._is_running = True
        logger.info(
            "scheduler_started",
            jobs=[job.id for job in self.scheduler.get_jobs()],
        )

    async def shutdown(self) -> None:
        """Shutdown the scheduler gracefully."""
        if not self._is_running:
            return

        logger.info("shutting_down_scheduler")
        self.scheduler.shutdown(wait=True)
        self._is_running = False
        logger.info("scheduler_shutdown_complete")

    async def _collect_prices_job(self) -> None:
        """Background job to collect cryptocurrency prices."""
        logger.debug("price_collection_job_started")
        async with AsyncSessionLocal() as session:
            try:
                collector = PriceCollectorService(session)
                await collector.collect_prices()
            except Exception as e:
                logger.error("price_collection_job_failed", error=str(e), exc_info=True)

    async def _evaluate_alerts_job(self) -> None:
        """Background job to evaluate alerts."""
        logger.debug("alert_evaluation_job_started")
        async with AsyncSessionLocal() as session:
            try:
                engine = AlertEngine(session)
                await engine.evaluate_alerts()
            except Exception as e:
                logger.error("alert_evaluation_job_failed", error=str(e), exc_info=True)

    async def _cleanup_old_data_job(self) -> None:
        """Background job to cleanup old data from database."""
        logger.info("cleanup_job_started")
        async with AsyncSessionLocal() as session:
            try:
                # Cleanup old price history (90 days)
                await session.execute(
                    """
                    DELETE FROM price_history
                    WHERE timestamp < datetime('now', '-90 days')
                    """
                )

                # Cleanup old alert logs (30 days)
                await session.execute(
                    """
                    DELETE FROM alert_logs
                    WHERE triggered_at < datetime('now', '-30 days')
                    """
                )

                await session.commit()
                logger.info("cleanup_job_completed")

            except Exception as e:
                logger.error("cleanup_job_failed", error=str(e), exc_info=True)
                await session.rollback()


# Global scheduler instance
scheduler = BackgroundScheduler()
