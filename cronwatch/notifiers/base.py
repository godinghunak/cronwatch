"""Base notifier interface for cronwatch alert delivery."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class AlertPayload:
    """Structured alert message sent to notifiers."""

    job_name: str
    reason: str  # 'missed_schedule' | 'failure_threshold' | 'never_ran'
    last_seen: Optional[datetime]
    consecutive_failures: int
    cron_expression: str
    timestamp: datetime

    def summary(self) -> str:
        last = self.last_seen.isoformat() if self.last_seen else "never"
        return (
            f"[cronwatch] ALERT for job '{self.job_name}': {self.reason} | "
            f"last_seen={last} | failures={self.consecutive_failures} | "
            f"cron='{self.cron_expression}'"
        )


class BaseNotifier(ABC):
    """Abstract base class that all notifier backends must implement."""

    @abstractmethod
    def send(self, payload: AlertPayload) -> None:
        """Deliver an alert.  Implementations should not raise on transient errors;
        they should log and swallow them so other notifiers still run."""
        ...
