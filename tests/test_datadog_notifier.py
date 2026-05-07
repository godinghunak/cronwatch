from __future__ import annotations

import json
import unittest
from datetime import datetime, timezone
from io import BytesIO
from unittest.mock import MagicMock, patch

from cronwatch.notifiers.base import AlertPayload
from cronwatch.notifiers.datadog_notifier import DatadogConfig, DatadogNotifier


def _utc(*args) -> datetime:
    return datetime(*args, tzinfo=timezone.utc)


def config(**kwargs) -> DatadogConfig:
    return DatadogConfig(api_key="test-api-key", **kwargs)


def payload(**kwargs) -> AlertPayload:
    defaults = dict(
        job_name="nightly-backup",
        reason="missed schedule",
        last_seen=_utc(2024, 1, 10, 2, 0, 0),
        consecutive_failures=0,
    )
    defaults.update(kwargs)
    return AlertPayload(**defaults)


def _mock_response(status: int = 202) -> MagicMock:
    resp = MagicMock()
    resp.status = status
    resp.__enter__ = lambda s: s
    resp.__exit__ = MagicMock(return_value=False)
    return resp


class TestDatadogNotifier(unittest.TestCase):

    @patch("cronwatch.notifiers.datadog_notifier.urllib.request.urlopen")
    def test_send_posts_to_datadog(self, mock_urlopen):
        mock_urlopen.return_value = _mock_response(202)
        notifier = DatadogNotifier(config())
        notifier.send(payload())
        mock_urlopen.assert_called_once()
        req = mock_urlopen.call_args[0][0]
        self.assertEqual(req.full_url, "https://api.datadoghq.com/api/v1/events")
        self.assertEqual(req.get_header("Dd-api-key"), "test-api-key")
        body = json.loads(req.data)
        self.assertIn("nightly-backup", body["title"])
        self.assertEqual(body["alert_type"], "error")

    @patch("cronwatch.notifiers.datadog_notifier.urllib.request.urlopen")
    def test_tags_include_job_name(self, mock_urlopen):
        mock_urlopen.return_value = _mock_response(202)
        notifier = DatadogNotifier(config(tags=["env:prod", "team:ops"]))
        notifier.send(payload())
        body = json.loads(mock_urlopen.call_args[0][0].data)
        self.assertIn("job:nightly-backup", body["tags"])
        self.assertIn("env:prod", body["tags"])

    @patch("cronwatch.notifiers.datadog_notifier.urllib.request.urlopen")
    def test_app_key_header_sent_when_provided(self, mock_urlopen):
        mock_urlopen.return_value = _mock_response(202)
        notifier = DatadogNotifier(config(app_key="my-app-key"))
        notifier.send(payload())
        req = mock_urlopen.call_args[0][0]
        self.assertEqual(req.get_header("Dd-application-key"), "my-app-key")

    @patch("cronwatch.notifiers.datadog_notifier.urllib.request.urlopen")
    def test_host_included_when_set(self, mock_urlopen):
        mock_urlopen.return_value = _mock_response(202)
        notifier = DatadogNotifier(config(host="worker-01"))
        notifier.send(payload())
        body = json.loads(mock_urlopen.call_args[0][0].data)
        self.assertEqual(body["host"], "worker-01")

    @patch("cronwatch.notifiers.datadog_notifier.urllib.request.urlopen")
    def test_http_error_does_not_raise(self, mock_urlopen):
        import urllib.error
        mock_urlopen.side_effect = urllib.error.HTTPError(
            url="", code=403, msg="Forbidden", hdrs=None, fp=None
        )
        notifier = DatadogNotifier(config())
        # Should log and not raise
        notifier.send(payload())

    @patch("cronwatch.notifiers.datadog_notifier.urllib.request.urlopen")
    def test_custom_base_url(self, mock_urlopen):
        mock_urlopen.return_value = _mock_response(202)
        eu_url = "https://api.datadoghq.eu/api/v1/events"
        notifier = DatadogNotifier(config(base_url=eu_url))
        notifier.send(payload())
        req = mock_urlopen.call_args[0][0]
        self.assertEqual(req.full_url, eu_url)


if __name__ == "__main__":
    unittest.main()
