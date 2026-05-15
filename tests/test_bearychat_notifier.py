"""Tests for BearyChatNotifier."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest

from cronwatch.notifiers.base import AlertPayload
from cronwatch.notifiers.bearychat_notifier import BearyChatNotifier, BearyyChatConfig


def _utc(year: int, month: int, day: int, hour: int = 0) -> datetime:
    return datetime(year, month, day, hour, tzinfo=timezone.utc)


@pytest.fixture()
def config() -> BearyyChatConfig:
    return BearyyChatConfig(
        webhook_url="https://hook.bearychat.com/abc123",
        channel="ops-alerts",
    )


@pytest.fixture()
def payload() -> AlertPayload:
    return AlertPayload(
        job_name="nightly-backup",
        reason="missed schedule",
        failure_count=0,
        last_seen=_utc(2024, 1, 15, 3),
    )


def _mock_response(status: int = 200) -> MagicMock:
    resp = MagicMock()
    resp.status = status
    resp.__enter__ = lambda s: s
    resp.__exit__ = MagicMock(return_value=False)
    return resp


class TestBearyChatNotifier:
    def test_send_posts_to_webhook(self, config, payload):
        notifier = BearyChatNotifier(config)
        with patch("urllib.request.urlopen", return_value=_mock_response()) as mock_open:
            notifier.send(payload)
        mock_open.assert_called_once()
        req = mock_open.call_args[0][0]
        assert req.full_url == config.webhook_url
        assert req.get_header("Content-type") == "application/json"

    def test_message_contains_job_name(self, config, payload):
        notifier = BearyChatNotifier(config)
        msg = notifier._build_message(payload)
        assert "nightly-backup" in json.dumps(msg)

    def test_message_contains_reason(self, config, payload):
        notifier = BearyChatNotifier(config)
        msg = notifier._build_message(payload)
        assert "missed schedule" in json.dumps(msg)

    def test_channel_included_when_set(self, config, payload):
        notifier = BearyChatNotifier(config)
        msg = notifier._build_message(payload)
        assert msg["channel"] == "ops-alerts"

    def test_channel_omitted_when_none(self, payload):
        cfg = BearyyChatConfig(webhook_url="https://hook.bearychat.com/xyz")
        notifier = BearyChatNotifier(cfg)
        msg = notifier._build_message(payload)
        assert "channel" not in msg

    def test_raises_on_non_2xx(self, config, payload):
        notifier = BearyChatNotifier(config)
        with patch(
            "urllib.request.urlopen", return_value=_mock_response(status=500)
        ):
            with pytest.raises(RuntimeError, match="HTTP 500"):
                notifier.send(payload)

    def test_last_seen_never_when_none(self, config):
        p = AlertPayload(
            job_name="db-dump",
            reason="never ran",
            failure_count=0,
            last_seen=None,
        )
        notifier = BearyChatNotifier(config)
        msg = notifier._build_message(p)
        assert "never" in json.dumps(msg)
