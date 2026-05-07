"""Tests for SlackNotifier."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest

from cronwatch.notifiers.base import AlertPayload
from cronwatch.notifiers.slack_notifier import SlackConfig, SlackNotifier


def _utc(*args) -> datetime:
    return datetime(*args, tzinfo=timezone.utc)


@pytest.fixture()
def payload() -> AlertPayload:
    return AlertPayload(
        job_name="nightly-backup",
        reason="missed schedule",
        last_seen=_utc(2024, 1, 10, 2, 0, 0),
        consecutive_failures=0,
    )


@pytest.fixture()
def config() -> SlackConfig:
    return SlackConfig(webhook_url="https://hooks.slack.com/services/TEST/WEBHOOK")


def _mock_response(status: int = 200):
    resp = MagicMock()
    resp.status = status
    resp.__enter__ = lambda s: s
    resp.__exit__ = MagicMock(return_value=False)
    return resp


def test_send_posts_to_webhook(config, payload):
    notifier = SlackNotifier(config)
    with patch("urllib.request.urlopen", return_value=_mock_response(200)) as mock_open:
        notifier.send(payload)

    mock_open.assert_called_once()
    request_obj = mock_open.call_args[0][0]
    assert request_obj.full_url == config.webhook_url
    assert request_obj.method == "POST"
    body = json.loads(request_obj.data.decode())
    assert "nightly-backup" in body["text"]
    assert body["username"] == "CronWatch"


def test_channel_included_when_set(payload):
    cfg = SlackConfig(webhook_url="https://hooks.slack.com/x", channel="#alerts")
    notifier = SlackNotifier(cfg)
    with patch("urllib.request.urlopen", return_value=_mock_response()) as mock_open:
        notifier.send(payload)
    body = json.loads(mock_open.call_args[0][0].data.decode())
    assert body["channel"] == "#alerts"


def test_no_send_when_webhook_url_empty(payload):
    cfg = SlackConfig(webhook_url="")
    notifier = SlackNotifier(cfg)
    with patch("urllib.request.urlopen") as mock_open:
        notifier.send(payload)
    mock_open.assert_not_called()


def test_url_error_is_logged_not_raised(config, payload):
    import urllib.error

    notifier = SlackNotifier(config)
    with patch("urllib.request.urlopen", side_effect=urllib.error.URLError("timeout")):
        # Should not raise
        notifier.send(payload)


def test_summary_in_message_body(config, payload):
    notifier = SlackNotifier(config)
    with patch("urllib.request.urlopen", return_value=_mock_response()) as mock_open:
        notifier.send(payload)
    body = json.loads(mock_open.call_args[0][0].data.decode())
    assert payload.summary() == body["text"]
