"""
Asynchronous background scheduler for Prometheus daily alignment digests.
Runs automated cron triggers (e.g. 08:00 AM daily briefing) and background fleet checks.
"""

import asyncio
import logging
from datetime import datetime, timezone
from typing import Optional
from app.security.abac_guard import UserContext
from app.workflows.prometheus_flow import PrometheusWorkflow

logger = logging.getLogger(__name__)


class PrometheusScheduler:
    """
    Background scheduler for scheduled alignment digests and continuous telemetry scans.
    """

    def __init__(self, interval_seconds: int = 3600):
        self._interval = interval_seconds
        self._task: Optional[asyncio.Task] = None
        self._is_running = False

    async def start(self):
        if self._is_running:
            return
        self._is_running = True
        self._task = asyncio.create_task(self._schedule_loop())
        logger.info("⏱️ [PrometheusScheduler] Background cron scheduler started.")

    async def stop(self):
        self._is_running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("⏱️ [PrometheusScheduler] Background cron scheduler stopped.")

    async def _schedule_loop(self):
        while self._is_running:
            try:
                now = datetime.now(timezone.utc)
                # Check for 08:00 AM UTC (or trigger periodic interval digest)
                logger.info(f"⏱️ [PrometheusScheduler] Running scheduled telemetry check at {now.isoformat()}...")
                
                system_user = UserContext(
                    user_id="cron-system",
                    username="prometheus-cron",
                    is_authenticated=True,
                    org_scopes={"engineering", "platform"},
                )
                await PrometheusWorkflow.run(
                    user=system_user,
                    query="Daily scheduled alignment digest execution",
                )

                await asyncio.sleep(self._interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"❌ [PrometheusScheduler] Error in background execution: {e}")
                await asyncio.sleep(60)


scheduler = PrometheusScheduler()
