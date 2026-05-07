"""Tests for TeamsNotifier."""

from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest

from cronwatch.notifiers.base import AlertPayload
from cronwatch.notifiers.teams_notifier import TeamsConfig, TeamsNotifier


def _utc(*args) -> datetime:
    return datetime(*args, tzinfo=timezone.utc)


@pytest.fixture()
def config() -> TeamsConfig:
    return TeamsConfig(webhook_url="https://outlook.office.com/webhook/test")


@pytest.fixture()
def payload() -> AlertPayload:
    return AlertPayload(
        job_name="backup",
        reason="missed schedule",
        last_seen=_utc(2024, 1, 10, 12, 0, 0),
        consecutive_failures=0,
    )


def _mock_response(status_code: int = 200) -> MagicMock:
    resp = MagicMock()
    resp.status_code = status_code
    resp.raise_for_status = MagicMock(
        side_effect=None if status_code < 400 else Exception("HTTP Error")
    )
    return resp


def test_send_posts_to_webhook(config, payload):
    with patch("cronwatch.notifiers.teams_notifier.requests.post") as mock_post:
        mock_post.return_value = _mock_response(200)
        notifier = TeamsNotifier(config)
        notifier.send(payload)

    mock_post.assert_called_once()
    url, kwargs = mock_post.call_args[0][0], mock_post.call_args[1]
    assert url == config.webhook_url
    assert "json" in kwargs


def test_message_contains_job_name(config, payload):
    notifier = TeamsNotifier(config)
    body = notifier._build_message(payload)
    assert payload.job_name in body["title"]
    facts = body["sections"][0]["facts"]
    job_fact = next(f for f in facts if f["name"] == "Job")
    assert job_fact["value"] == payload.job_name


def test_message_contains_reason(config, payload):
    notifier = TeamsNotifier(config)
    body = notifier._build_message(payload)
    facts = body["sections"][0]["facts"]
    reason_fact = next(f for f in facts if f["name"] == "Reason")
    assert reason_fact["value"] == payload.reason


def test_no_send_when_no_webhook_url(payload):
    notifier = TeamsNotifier(TeamsConfig(webhook_url=""))
    with patch("cronwatch.notifiers.teams_notifier.requests.post") as mock_post:
        notifier.send(payload)
    mock_post.assert_not_called()


def test_mention_emails_included_in_text(payload):
    cfg = TeamsConfig(
        webhook_url="https://outlook.office.com/webhook/test",
        mention_emails=["alice@example.com", "bob@example.com"],
    )
    notifier = TeamsNotifier(cfg)
    body = notifier._build_message(payload)
    assert "<at>alice@example.com</at>" in body["text"]
    assert "<at>bob@example.com</at>" in body["text"]


def test_http_error_is_logged_not_raised(config, payload, caplog):
    bad_resp = _mock_response(500)
    bad_resp.raise_for_status.side_effect = Exception("500 Server Error")
    with patch("cronwatch.notifiers.teams_notifier.requests.post", return_value=bad_resp):
        notifier = TeamsNotifier(config)
        notifier.send(payload)  # should not raise
    assert "failed to send" in caplog.text.lower()
