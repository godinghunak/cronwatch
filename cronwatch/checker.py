"""Periodic checker that inspects the registry and fires alerts on anomalies."""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Callable, List

from cronwatch.job_registry import JobRecord, JobRegistry

logger = logging.getLogger(__name__)

AlertCallback = Callable[[str, str], None]  # (job_name, message)


class CronChecker:
    """Inspects all registered jobs and triggers alert callbacks when needed."""

    def __init__(
        self,
        registry: JobRegistry,
        alert_callbacks: List[AlertCallback],
        tolerance_seconds: int = 60,
        failure_threshold: int = 1,
    ) -> None:
        self.registry = registry
        self.alert_callbacks = alert_callbacks
        self.tolerance_seconds = tolerance_seconds
        self.failure_threshold = failure_threshold

    def check_all(self) -> None:
        """Run checks across every registered job."""
        for record in self.registry.all_jobs():
            self._check_job(record)

    def _check_job(self, record: JobRecord) -> None:
        if record.failure_count >= self.failure_threshold:
            msg = (
                f"Job '{record.name}' has failed {record.failure_count} time(s). "
                f"Last error: {record.last_error}"
            )
            self._alert(record.name, msg)
            return

        if record.last_seen is None:
            msg = f"Job '{record.name}' has never reported a heartbeat."
            self._alert(record.name, msg)
            return

        if record.schedule.is_missed(record.last_seen, self.tolerance_seconds):
            expected = record.schedule.last_expected_run()
            msg = (
                f"Job '{record.name}' missed its scheduled run at "
                f"{expected.isoformat()}. Last seen: {record.last_seen.isoformat()}."
            )
            self._alert(record.name, msg)

    def _alert(self, job_name: str, message: str) -> None:
        logger.warning("ALERT [%s]: %s", job_name, message)
        for cb in self.alert_callbacks:
            try:
                cb(job_name, message)
            except Exception:  # noqa: BLE001
                logger.exception("Alert callback failed for job '%s'", job_name)
