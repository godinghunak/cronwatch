"""HTTP webhook notifier — posts a JSON payload to a configurable URL."""

import json
import logging
import urllib.error
import urllib.request
from typing import Optional

from cronwatch.notifiers.base import AlertPayload, BaseNotifier

logger = logging.getLogger("cronwatch.notifiers.webhook")


class WebhookNotifier(BaseNotifier):
    """POST alert details as JSON to an HTTP(S) endpoint.

    Args:
        url: Destination URL (e.g. a Slack incoming-webhook URL).
        timeout: Request timeout in seconds (default 5).
        extra_headers: Optional dict of additional HTTP headers.
    """

    def __init__(
        self,
        url: str,
        timeout: int = 5,
        extra_headers: Optional[dict] = None,
    ) -> None:
        self._url = url
        self._timeout = timeout
        self._headers = {"Content-Type": "application/json"}
        if extra_headers:
            self._headers.update(extra_headers)

    def send(self, payload: AlertPayload) -> None:
        body = {
            "job_name": payload.job_name,
            "reason": payload.reason,
            "last_seen": payload.last_seen.isoformat() if payload.last_seen else None,
            "consecutive_failures": payload.consecutive_failures,
            "cron_expression": payload.cron_expression,
            "timestamp": payload.timestamp.isoformat(),
            "summary": payload.summary(),
        }
        data = json.dumps(body).encode()
        req = urllib.request.Request(self._url, data=data, headers=self._headers)
        try:
            with urllib.request.urlopen(req, timeout=self._timeout):
                pass
        except urllib.error.URLError as exc:
            logger.warning("WebhookNotifier failed to deliver alert: %s", exc)
        except Exception as exc:  # noqa: BLE001
            logger.warning("WebhookNotifier unexpected error: %s", exc)
