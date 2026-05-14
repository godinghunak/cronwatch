"""Tests for ZulipNotifier."""
from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest
import requests

from cronwatch.notifiers.base import AlertPayload
from cronwatch.notifiers.zulip_notifier import ZulipConfig, ZulipNotifier


def _utc(*args) -> datetime:
    return datetime(*args, tzinfo=timezone.utc)


@pytest.fixture()
def config() -> ZulipConfig:
    return ZulipConfig(
        site_url="https://test.zulipchat.com",
        bot_email="bot@test.zulipchat.com",
        bot_api_key="secret-key",
        stream="alerts",
        topic="cronwatch",
    )


@pytest.fixture()
def payload() -> AlertPayload:
    return AlertPayload(
        job_name="backup",
        reason="missed schedule",
        last_seen=_utc(2024, 1, 1, 10, 0, 0),
        expected_at=_utc(2024, 1, 1, 11, 0, 0),
    )


@pytest.fixture()
def _mock_response():
    resp = MagicMock()
    resp.raise_for_status.return_value = None
    return resp


def test_send_posts_to_correct_url(config, payload, _mock_response):
    with patch("cronwatch.notifiers.zulip_notifier.requests.post", return_value=_mock_response) as mock_post:
        ZulipNotifier(config).send(payload)
    mock_post.assert_called_once()
    url = mock_post.call_args[0][0]
    assert url == "https://test.zulipchat.com/api/v1/messages"


def test_send_uses_basic_auth(config, payload, _mock_response):
    with patch("cronwatch.notifiers.zulip_notifier.requests.post", return_value=_mock_response) as mock_post:
        ZulipNotifier(config).send(payload)
    kwargs = mock_post.call_args[1]
    assert kwargs["auth"] == (config.bot_email, config.bot_api_key)


def test_send_includes_stream_and_topic(config, payload, _mock_response):
    with patch("cronwatch.notifiers.zulip_notifier.requests.post", return_value=_mock_response) as mock_post:
        ZulipNotifier(config).send(payload)
    data = mock_post.call_args[1]["data"]
    assert data["to"] == "alerts"
    assert data["topic"] == "cronwatch"
    assert data["type"] == "stream"


def test_send_message_contains_job_name(config, payload, _mock_response):
    with patch("cronwatch.notifiers.zulip_notifier.requests.post", return_value=_mock_response) as mock_post:
        ZulipNotifier(config).send(payload)
    content = mock_post.call_args[1]["data"]["content"]
    assert "backup" in content


def test_send_logs_error_on_request_exception(config, payload):
    with patch("cronwatch.notifiers.zulip_notifier.requests.post", side_effect=requests.ConnectionError("down")):
        # Should not raise
        ZulipNotifier(config).send(payload)


def test_site_url_trailing_slash_stripped():
    cfg = ZulipConfig(
        site_url="https://test.zulipchat.com/",
        bot_email="bot@test.zulipchat.com",
        bot_api_key="key",
        stream="general",
    )
    assert cfg.site_url == "https://test.zulipchat.com"
