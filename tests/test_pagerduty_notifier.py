"""Tests for the PagerDuty notifier."""

from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest
import requests

from cronwatch.notifiers.base import AlertPayload
from cronwatch.notifiers.pagerduty_notifier import (
    PAGERDUTY_EVENTS_URL,
    PagerDutyConfig,
    PagerDutyNotifier,
)


def _utc(*args) -> datetime:
    return datetime(*args, tzinfo=timezone.utc)


@pytest.fixture()
def config() -> PagerDutyConfig:
    return PagerDutyConfig(integration_key="test-routing-key-abc123", severity="error")


@pytest.fixture()
def payload() -> AlertPayload:
    return AlertPayload(
        job_name="backup-job",
        reason="missed_schedule",
        last_seen=_utc(2024, 1, 15, 10, 0, 0),
        consecutive_failures=0,
    )


def _mock_response(status_code: int = 202) -> MagicMock:
    resp = MagicMock()
    resp.status_code = status_code
    resp.raise_for_status = MagicMock()
    if status_code >= 400:
        resp.raise_for_status.side_effect = requests.HTTPError(response=resp)
    return resp


def test_send_posts_to_pagerduty(config, payload):
    notifier = PagerDutyNotifier(config)
    with patch("cronwatch.notifiers.pagerduty_notifier.requests.post") as mock_post:
        mock_post.return_value = _mock_response(202)
        notifier.send(payload)

    mock_post.assert_called_once()
    call_kwargs = mock_post.call_args
    assert call_kwargs[0][0] == PAGERDUTY_EVENTS_URL


def test_event_body_contains_routing_key(config, payload):
    notifier = PagerDutyNotifier(config)
    with patch("cronwatch.notifiers.pagerduty_notifier.requests.post") as mock_post:
        mock_post.return_value = _mock_response(202)
        notifier.send(payload)

    body = mock_post.call_args[1]["json"]
    assert body["routing_key"] == "test-routing-key-abc123"
    assert body["event_action"] == "trigger"


def test_dedup_key_includes_job_name(config, payload):
    notifier = PagerDutyNotifier(config)
    with patch("cronwatch.notifiers.pagerduty_notifier.requests.post") as mock_post:
        mock_post.return_value = _mock_response(202)
        notifier.send(payload)

    body = mock_post.call_args[1]["json"]
    assert body["dedup_key"] == "cronwatch-backup-job"


def test_severity_is_forwarded(config, payload):
    notifier = PagerDutyNotifier(config)
    with patch("cronwatch.notifiers.pagerduty_notifier.requests.post") as mock_post:
        mock_post.return_value = _mock_response(202)
        notifier.send(payload)

    body = mock_post.call_args[1]["json"]
    assert body["payload"]["severity"] == "error"


def test_http_error_is_logged_not_raised(config, payload):
    notifier = PagerDutyNotifier(config)
    with patch("cronwatch.notifiers.pagerduty_notifier.requests.post") as mock_post:
        mock_post.return_value = _mock_response(400)
        # Should not raise
        notifier.send(payload)


def test_extra_details_merged_into_event(payload):
    cfg = PagerDutyConfig(
        integration_key="key-xyz",
        extra_details={"env": "production", "team": "platform"},
    )
    notifier = PagerDutyNotifier(cfg)
    with patch("cronwatch.notifiers.pagerduty_notifier.requests.post") as mock_post:
        mock_post.return_value = _mock_response(202)
        notifier.send(payload)

    details = mock_post.call_args[1]["json"]["payload"]["custom_details"]
    assert details["env"] == "production"
    assert details["team"] == "platform"
    assert details["reason"] == "missed_schedule"
