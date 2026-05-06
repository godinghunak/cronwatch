"""Cron schedule parser and missed-run detector."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from croniter import croniter


class CronSchedule:
    """Wraps a cron expression and tracks expected run times."""

    def __init__(self, expression: str, job_name: str) -> None:
        if not croniter.is_valid(expression):
            raise ValueError(f"Invalid cron expression for job '{job_name}': {expression}")
        self.expression = expression
        self.job_name = job_name

    def last_expected_run(self, reference: Optional[datetime] = None) -> datetime:
        """Return the most recent scheduled datetime before *reference* (UTC)."""
        ref = reference or datetime.now(timezone.utc)
        it = croniter(self.expression, ref)
        return it.get_prev(datetime)

    def next_expected_run(self, reference: Optional[datetime] = None) -> datetime:
        """Return the next scheduled datetime after *reference* (UTC)."""
        ref = reference or datetime.now(timezone.utc)
        it = croniter(self.expression, ref)
        return it.get_next(datetime)

    def is_missed(self, last_seen: datetime, tolerance_seconds: int = 60) -> bool:
        """Return True if the job missed its last expected run.

        A run is considered missed when the last recorded execution is older
        than the most recently scheduled time minus *tolerance_seconds*.
        """
        expected = self.last_expected_run()
        deadline = expected.timestamp() - tolerance_seconds
        return last_seen.timestamp() < deadline
