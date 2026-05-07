"""Base classes and shared data types for cronwatch notifiers."""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class AlertPayload:
    """Carries all context needed to compose an alert message."""

    job_name: str
    reason: str
    last_seen: Optional[datetime]
    exit_code: Optional[int] = None

    def summary(self) -> str:
        """Return a human-readable one-line summary of the alert."""
        ts = self.last_seen.isoformat() if self.last_seen else "never"
        parts = [
            f"Job '{self.job_name}' alert: {self.reason}.",
            f"Last seen: {ts}.",
        ]
        if self.exit_code is not None:
            parts.append(f"Exit code: {self.exit_code}.")
        return " ".join(parts)


class BaseNotifier(ABC):
    """Abstract base class for all notifiers."""

    @abstractmethod
    def send(self, payload: AlertPayload) -> None:
        """Dispatch an alert.  Implementations must not raise on delivery failure."""
