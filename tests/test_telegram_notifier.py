"""Tests for TelegramNotifier."""

from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest
import requests

from cronwatch.notifiers.base import AlertPayload
from cronwatch.notifiers.telegram_notifier import TelegramConfig, TelegramNotifier


def _utc(*args) -> datetime:
    return datetime(*args, tzinfo=timezone.utc)


@pytest.fixture()
def config() -> TelegramConfig:
    return TelegramConfig(
        bot_token="test-bot-token",
        chat_ids=["111", "222"],
    )


@pytest.fixture()
def payload() -> AlertPayload:
    return AlertPayload(
        job_name="nightly-backup",
        reason="missed schedule",
        triggered_at=_utc(2024, 6, 1, 3, 0, 0),
        last_seen=_utc(2024, 5, 31, 3, 0, 0),
        details="Expected at 03:00 UTC",
    )


def _mock_response(status_code: int = 200) -> MagicMock:
    resp = MagicMock()
    resp.status_code = status_code
    resp.raise_for_status = MagicMock(
        side_effect=None if status_code < 400 else requests.HTTPError()
    )
    return resp


def test_send_posts_to_each_chat_id(config, payload):
    notifier = TelegramNotifier(config)
    with patch("cronwatch.notifiers.telegram_notifier.requests.post") as mock_post:
        mock_post.return_value = _mock_response(200)
        notifier.send(payload)

    assert mock_post.call_count == 2
    urls = [call.args[0] for call in mock_post.call_args_list]
    assert all("test-bot-token" in url for url in urls)
    bodies = [call.kwargs["json"] for call in mock_post.call_args_list]
    assert {b["chat_id"] for b in bodies} == {"111", "222"}


def test_no_send_when_no_chat_ids(payload):
    cfg = TelegramConfig(bot_token="tok", chat_ids=[])
    notifier = TelegramNotifier(cfg)
    with patch("cronwatch.notifiers.telegram_notifier.requests.post") as mock_post:
        notifier.send(payload)
    mock_post.assert_not_called()


def test_message_contains_job_name_and_reason(config, payload):
    notifier = TelegramNotifier(config)
    text = notifier._build_message(payload)
    assert "nightly-backup" in text
    assert "missed schedule" in text


def test_message_contains_last_seen_when_present(config, payload):
    notifier = TelegramNotifier(config)
    text = notifier._build_message(payload)
    assert "Last seen" in text


def test_message_omits_last_seen_when_none(config):
    p = AlertPayload(
        job_name="job",
        reason="never ran",
        triggered_at=_utc(2024, 6, 1, 0, 0, 0),
        last_seen=None,
    )
    notifier = TelegramNotifier(config)
    text = notifier._build_message(p)
    assert "Last seen" not in text


def test_http_error_is_logged_not_raised(config, payload, caplog):
    notifier = TelegramNotifier(config)
    bad_resp = _mock_response(500)
    bad_resp.raise_for_status.side_effect = requests.HTTPError("500")
    with patch("cronwatch.notifiers.telegram_notifier.requests.post", return_value=bad_resp):
        notifier.send(payload)  # must not raise
    assert any("failed" in r.message.lower() for r in caplog.records)
