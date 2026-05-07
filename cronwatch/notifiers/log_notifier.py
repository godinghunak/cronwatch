"""Simple notifier that writes alerts to a Python logger."""

import logging
from cronwatch.notifiers.base import AlertPayload, BaseNotifier

logger = logging.getLogger("cronwatch.alerts")


class LogNotifier(BaseNotifier):
    """Writes alert summaries to the Python logging system.

    Useful as a fallback or during development / testing.
    """

    def __init__(self, level: int = logging.WARNING) -> None:
        self._level = level

    def send(self, payload: AlertPayload) -> None:
        logger.log(self._level, payload.summary())
