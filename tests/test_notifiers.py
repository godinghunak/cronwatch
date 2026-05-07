"""Tests for cronwatch notifier backends."""

import json
import logging
import unittest
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

from cronwatch.notifiers import AlertPayload, LogNotifier, WebhookNotifier


def _payload(**kwargs) -> AlertPayload:
    defaults = dict(
        job_name="nightly-backup",
        reason="missed_schedule",
        last_seen=datetime(2024, 1, 1, 3, 0, tzinfo=timezone.utc),
        consecutive_failures=0,
        cron_expression="0 3 * * *",
        timestamp=datetime(2024, 1, 1, 4, 0, tzinfo=timezone.utc),
    )
    defaults.update(kwargs)
    return AlertPayload(**defaults)


class TestAlertPayload(unittest.TestCase):
    def test_summary_contains_job_name(self):
        p = _payload()
        assert "nightly-backup" in p.summary()

    def test_summary_contains_reason(self):
        p = _payload(reason="failure_threshold")
        assert "failure_threshold" in p.summary()

    def test_summary_never_ran(self):
        p = _payload(last_seen=None)
        assert "never" in p.summary()


class TestLogNotifier(unittest.TestCase):
    def test_send_logs_at_configured_level(self):
        notifier = LogNotifier(level=logging.ERROR)
        with self.assertLogs("cronwatch.alerts", level="ERROR") as cm:
            notifier.send(_payload())
        assert any("nightly-backup" in line for line in cm.output)

    def test_default_level_is_warning(self):
        notifier = LogNotifier()
        with self.assertLogs("cronwatch.alerts", level="WARNING") as cm:
            notifier.send(_payload())
        assert cm.output  # at least one record emitted


class TestWebhookNotifier(unittest.TestCase):
    def _make_notifier(self, url="https://hooks.example.com/test"):
        return WebhookNotifier(url=url, timeout=2)

    def test_send_posts_json_with_correct_fields(self):
        notifier = self._make_notifier()
        mock_response = MagicMock()
        mock_response.__enter__ = lambda s: s
        mock_response.__exit__ = MagicMock(return_value=False)

        with patch("urllib.request.urlopen", return_value=mock_response) as mock_open:
            notifier.send(_payload())

        mock_open.assert_called_once()
        request_obj = mock_open.call_args[0][0]
        body = json.loads(request_obj.data.decode())
        assert body["job_name"] == "nightly-backup"
        assert body["reason"] == "missed_schedule"
        assert "summary" in body

    def test_send_does_not_raise_on_network_error(self):
        import urllib.error

        notifier = self._make_notifier()
        with patch(
            "urllib.request.urlopen",
            side_effect=urllib.error.URLError("connection refused"),
        ):
            # Should swallow the error
            notifier.send(_payload())

    def test_extra_headers_forwarded(self):
        notifier = WebhookNotifier(
            url="https://hooks.example.com/test",
            extra_headers={"X-Api-Key": "secret"},
        )
        mock_response = MagicMock()
        mock_response.__enter__ = lambda s: s
        mock_response.__exit__ = MagicMock(return_value=False)
        with patch("urllib.request.urlopen", return_value=mock_response) as mock_open:
            notifier.send(_payload())
        request_obj = mock_open.call_args[0][0]
        assert request_obj.get_header("X-api-key") == "secret"


if __name__ == "__main__":
    unittest.main()
