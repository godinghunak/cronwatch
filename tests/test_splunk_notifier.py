"""Tests for SplunkNotifier."""

from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest

from cronwatch.notifiers.base import AlertPayload
from cronwatch.notifiers.splunk_notifier import SplunkConfig, SplunkNotifier


def _utc(*args) -> datetime:
    return datetime(*args, tzinfo=timezone.utc)


@pytest.fixture()
def config() -> SplunkConfig:
    return SplunkConfig(
        hec_url="https://splunk.example.com:8088/services/collector/event",
        token="test-hec-token",
        index="main",
    )


@pytest.fixture()
def payload() -> AlertPayload:
    return AlertPayload(
        job_name="nightly-backup",
        reason="missed_schedule",
        last_seen=_utc(2024, 1, 10, 2, 0, 0),
        consecutive_failures=0,
    )


def _mock_response(status_code: int = 200) -> MagicMock:
    resp = MagicMock()
    resp.status_code = status_code
    resp.raise_for_status = MagicMock()
    return resp


class TestSplunkNotifier:
    def test_send_posts_to_hec_url(self, config, payload):
        notifier = SplunkNotifier(config)
        with patch("requests.post", return_value=_mock_response()) as mock_post:
            notifier.send(payload)
        mock_post.assert_called_once()
        call_kwargs = mock_post.call_args
        assert call_kwargs[0][0] == config.hec_url

    def test_send_includes_auth_header(self, config, payload):
        notifier = SplunkNotifier(config)
        with patch("requests.post", return_value=_mock_response()) as mock_post:
            notifier.send(payload)
        headers = mock_post.call_args[1]["headers"]
        assert headers["Authorization"] == f"Splunk {config.token}"

    def test_event_contains_job_name(self, config, payload):
        notifier = SplunkNotifier(config)
        event = notifier._build_event(payload)
        assert event["event"]["job"] == "nightly-backup"

    def test_event_contains_index(self, config, payload):
        notifier = SplunkNotifier(config)
        event = notifier._build_event(payload)
        assert event["index"] == "main"

    def test_event_omits_index_when_not_set(self, payload):
        cfg = SplunkConfig(
            hec_url="https://splunk.example.com:8088/services/collector/event",
            token="tok",
        )
        notifier = SplunkNotifier(cfg)
        event = notifier._build_event(payload)
        assert "index" not in event

    def test_extra_fields_included_in_event(self, payload):
        cfg = SplunkConfig(
            hec_url="https://splunk.example.com:8088/services/collector/event",
            token="tok",
            extra_fields={"env": "production", "team": "platform"},
        )
        notifier = SplunkNotifier(cfg)
        event = notifier._build_event(payload)
        assert event["event"]["env"] == "production"
        assert event["event"]["team"] == "platform"

    def test_http_error_propagates(self, config, payload):
        import requests as req

        bad_resp = _mock_response(status_code=403)
        bad_resp.raise_for_status.side_effect = req.HTTPError("403")
        notifier = SplunkNotifier(config)
        with patch("requests.post", return_value=bad_resp):
            with pytest.raises(req.HTTPError):
                notifier.send(payload)
