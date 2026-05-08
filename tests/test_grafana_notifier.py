from __future__ import annotations

import json
import unittest
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

from cronwatch.notifiers.base import AlertPayload
from cronwatch.notifiers.grafana_notifier import GrafanaConfig, GrafanaNotifier


def _utc(*args) -> datetime:
    return datetime(*args, tzinfo=timezone.utc)


def config(**kwargs) -> GrafanaConfig:
    defaults = {"url": "https://grafana.example.com/api/webhook"}
    defaults.update(kwargs)
    return GrafanaConfig(**defaults)


def payload(**kwargs) -> AlertPayload:
    defaults = {
        "job_name": "nightly-backup",
        "reason": "missed schedule",
        "last_seen": _utc(2024, 1, 10, 3, 0, 0),
        "schedule": "0 2 * * *",
        "consecutive_failures": 0,
    }
    defaults.update(kwargs)
    return AlertPayload(**defaults)


def _mock_response(status: int = 200):
    resp = MagicMock()
    resp.status = status
    resp.__enter__ = lambda s: s
    resp.__exit__ = MagicMock(return_value=False)
    return resp


class TestGrafanaNotifier(unittest.TestCase):
    @patch("cronwatch.notifiers.grafana_notifier.urllib.request.urlopen")
    def test_send_posts_to_webhook(self, mock_urlopen):
        mock_urlopen.return_value = _mock_response(200)
        notifier = GrafanaNotifier(config())
        notifier.send(payload())
        mock_urlopen.assert_called_once()

    @patch("cronwatch.notifiers.grafana_notifier.urllib.request.urlopen")
    def test_request_body_contains_job_name(self, mock_urlopen):
        mock_urlopen.return_value = _mock_response(200)
        notifier = GrafanaNotifier(config())
        notifier.send(payload(job_name="db-cleanup"))
        req = mock_urlopen.call_args[0][0]
        body = json.loads(req.data.decode())
        assert body["labels"]["job"] == "db-cleanup"

    @patch("cronwatch.notifiers.grafana_notifier.urllib.request.urlopen")
    def test_api_key_added_as_bearer_token(self, mock_urlopen):
        mock_urlopen.return_value = _mock_response(200)
        notifier = GrafanaNotifier(config(api_key="secret-token"))
        notifier.send(payload())
        req = mock_urlopen.call_args[0][0]
        assert req.get_header("Authorization") == "Bearer secret-token"

    @patch("cronwatch.notifiers.grafana_notifier.urllib.request.urlopen")
    def test_tags_added_as_labels(self, mock_urlopen):
        mock_urlopen.return_value = _mock_response(200)
        notifier = GrafanaNotifier(config(tags=["env:production", "team:ops"]))
        notifier.send(payload())
        req = mock_urlopen.call_args[0][0]
        body = json.loads(req.data.decode())
        assert body["labels"]["env"] == "production"
        assert body["labels"]["team"] == "ops"

    @patch("cronwatch.notifiers.grafana_notifier.urllib.request.urlopen")
    def test_http_error_does_not_raise(self, mock_urlopen):
        import urllib.error
        mock_urlopen.side_effect = urllib.error.HTTPError(
            url="", code=500, msg="Server Error", hdrs=None, fp=None  # type: ignore[arg-type]
        )
        notifier = GrafanaNotifier(config())
        # Should log and return without raising
        notifier.send(payload())

    @patch("cronwatch.notifiers.grafana_notifier.urllib.request.urlopen")
    def test_state_is_alerting(self, mock_urlopen):
        mock_urlopen.return_value = _mock_response(200)
        notifier = GrafanaNotifier(config())
        notifier.send(payload())
        req = mock_urlopen.call_args[0][0]
        body = json.loads(req.data.decode())
        assert body["state"] == "alerting"


if __name__ == "__main__":
    unittest.main()
