"""Tests for GoogleChatNotifier."""

from __future__ import annotations

import json
import urllib.error
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest

from cronwatch.notifiers.base import AlertPayload
from cronwatch.notifiers.googlechat_notifier import GoogleChatConfig, GoogleChatNotifier


def _utc(year: int, month: int, day: int, hour: int = 0, minute: int = 0) -> datetime:
    return datetime(year, month, day, hour, minute, tzinfo=timezone.utc)


@pytest.fixture
def config() -> GoogleChatConfig:
    return GoogleChatConfig(webhook_url="https://chat.googleapis.com/v1/spaces/XXX/messages?key=abc")


@pytest.fixture
def payload() -> AlertPayload:
    return AlertPayload(
        job_name="nightly-backup",
        reason="missed schedule",
        last_seen=_utc(2024, 1, 10, 2, 0),
        expected_at=_utc(2024, 1, 11, 2, 0),
    )


def _mock_response(status: int = 200) -> MagicMock:
    resp = MagicMock()
    resp.status = status
    resp.__enter__ = lambda s: s
    resp.__exit__ = MagicMock(return_value=False)
    return resp


class TestGoogleChatNotifier:
    def test_send_posts_to_webhook(self, config: GoogleChatConfig, payload: AlertPayload) -> None:
        notifier = GoogleChatNotifier(config)
        with patch("urllib.request.urlopen", return_value=_mock_response()) as mock_open:
            notifier.send(payload)
        mock_open.assert_called_once()
        req = mock_open.call_args[0][0]
        assert req.full_url == config.webhook_url
        assert req.method == "POST"

    def test_request_body_contains_job_name(self, config: GoogleChatConfig, payload: AlertPayload) -> None:
        notifier = GoogleChatNotifier(config)
        with patch("urllib.request.urlopen", return_value=_mock_response()) as mock_open:
            notifier.send(payload)
        req = mock_open.call_args[0][0]
        body = json.loads(req.data.decode())
        header_title = body["cards"][0]["header"]["title"]
        assert "nightly-backup" in header_title

    def test_request_body_contains_reason(self, config: GoogleChatConfig, payload: AlertPayload) -> None:
        notifier = GoogleChatNotifier(config)
        with patch("urllib.request.urlopen", return_value=_mock_response()) as mock_open:
            notifier.send(payload)
        req = mock_open.call_args[0][0]
        body = json.loads(req.data.decode())
        subtitle = body["cards"][0]["header"]["subtitle"]
        assert "missed schedule" in subtitle

    def test_non_200_status_logs_warning(self, config: GoogleChatConfig, payload: AlertPayload, caplog) -> None:
        notifier = GoogleChatNotifier(config)
        with patch("urllib.request.urlopen", return_value=_mock_response(status=400)):
            import logging
            with caplog.at_level(logging.WARNING):
                notifier.send(payload)
        assert any("400" in r.message for r in caplog.records)

    def test_url_error_logs_error(self, config: GoogleChatConfig, payload: AlertPayload, caplog) -> None:
        notifier = GoogleChatNotifier(config)
        with patch("urllib.request.urlopen", side_effect=urllib.error.URLError("connection refused")):
            import logging
            with caplog.at_level(logging.ERROR):
                notifier.send(payload)
        assert any("connection refused" in r.message for r in caplog.records)

    def test_extra_headers_forwarded(self, payload: AlertPayload) -> None:
        cfg = GoogleChatConfig(
            webhook_url="https://chat.googleapis.com/hook",
            extra_headers={"X-Custom-Header": "cronwatch"},
        )
        notifier = GoogleChatNotifier(cfg)
        with patch("urllib.request.urlopen", return_value=_mock_response()) as mock_open:
            notifier.send(payload)
        req = mock_open.call_args[0][0]
        assert req.get_header("X-custom-header") == "cronwatch"
