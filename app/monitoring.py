from __future__ import annotations

import asyncio
import logging
from datetime import datetime

from app.services import (
    create_alert_if_needed,
    get_latest_vital,
    list_monitoring_sessions,
    save_vital_reading,
)
from app.simulator import build_next_vitals

logger = logging.getLogger(__name__)


class MonitoringEngine:
    def __init__(self) -> None:
        self._task: asyncio.Task | None = None
        self._running = False
        self._last_run: dict[str, float] = {}

    async def start(self) -> None:
        if self._running:
            return

        self._running = True
        self._task = asyncio.create_task(self._run_loop())
        logger.info("Monitoring engine started")

    async def stop(self) -> None:
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("Monitoring engine stopped")

    async def _run_loop(self) -> None:
        while self._running:
            try:
                await self._tick()
            except Exception as exc:
                logger.exception("Monitoring loop error: %s", exc)

            await asyncio.sleep(1)

    async def _tick(self) -> None:
        loop_time = asyncio.get_event_loop().time()
        sessions = list_monitoring_sessions()

        for session in sessions:
            if not session.active:
                continue

            last_run = self._last_run.get(session.patient_id, 0)
            due = (loop_time - last_run) >= session.interval_seconds

            if not due:
                continue

            previous = get_latest_vital(session.patient_id)
            vital = build_next_vitals(
                patient_id=session.patient_id,
                previous=previous,
                trend=session.trend,
            )
            vital.timestamp = datetime.utcnow()

            saved_vital = save_vital_reading(vital)
            alert = create_alert_if_needed(saved_vital)

            self._last_run[session.patient_id] = loop_time

            if alert:
                logger.info(
                    "Alert created for patient %s with severity %s",
                    session.patient_id,
                    alert.severity,
                )


monitoring_engine = MonitoringEngine()