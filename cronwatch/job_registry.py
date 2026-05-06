"""In-memory registry that tracks monitored cron jobs and their last heartbeat."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, Optional

from cronwatch.scheduler import CronSchedule


@dataclass
class JobRecord:
    name: str
    schedule: CronSchedule
    last_seen: Optional[datetime] = None
    failure_count: int = 0
    last_error: Optional[str] = None


class JobRegistry:
    """Manages the collection of watched jobs."""

    def __init__(self) -> None:
        self._jobs: Dict[str, JobRecord] = {}

    def register(self, name: str, cron_expression: str) -> JobRecord:
        """Register a new job or update its schedule."""
        schedule = CronSchedule(cron_expression, name)
        record = JobRecord(name=name, schedule=schedule)
        self._jobs[name] = record
        return record

    def heartbeat(self, name: str) -> None:
        """Record a successful execution for *name*."""
        record = self._get_or_raise(name)
        record.last_seen = datetime.now(timezone.utc)
        record.failure_count = 0
        record.last_error = None

    def record_failure(self, name: str, error: str) -> None:
        """Increment failure counter and store the error message."""
        record = self._get_or_raise(name)
        record.last_seen = datetime.now(timezone.utc)
        record.failure_count += 1
        record.last_error = error

    def all_jobs(self) -> list[JobRecord]:
        return list(self._jobs.values())

    def get(self, name: str) -> Optional[JobRecord]:
        return self._jobs.get(name)

    def _get_or_raise(self, name: str) -> JobRecord:
        if name not in self._jobs:
            raise KeyError(f"Job '{name}' is not registered.")
        return self._jobs[name]
