"""Tests for the OpsGenie notifier."""
from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest
import requests

from cronwatch.notifiers.base import AlertPayload
from cronwatch.notifiers.opsgenie_notifier import OpsGenieConfig, OpsGenieNotifier


def _utc(*args) -> datetime:
    return datetime(*args, tzinfo=timezone.utc)


@pytest.fixture()
def config() -> OpsGenieConfig:
    return OpsGenieConfig(
        api_key="test-api-key",
        responders=[{"type": "team", "name": "platform"}],
        tags=["cron", "prod"],
        priority="P2",
    )


@pytest.fixture()
def payload() -> AlertPayload:
    return AlertPayload(
        job_name="backup-job",
        reason="missed schedule",
        last_seen=_utc(2024, 1, 10, 6, 0, 0),
        exit_code=None,
    )


def _mock_response(status_code: int = 202) -> MagicMock:
    resp = MagicMock()
    resp.status_code = status_code
    resp.raise_for_status = MagicMock(
        side_effect=requests.HTTPError() if status_code >= 400 else None
    )
    return resp


def test_send_posts_to_opsgenie(config, payload):
    notifier = OpsGenieNotifier(config)
    with patch("cronwatch.notifiers.opsgenie_notifier.requests.post") as mock_post:
        mock_post.return_value = _mock_response(202)
        notifier.send(payload)

    mock_post.assert_called_once()
    _, kwargs = mock_post.call_args
    assert kwargs["json"]["alias"] == "cronwatch-backup-job"
    assert kwargs["json"]["priority"] == "P2"
    assert kwargs["headers"]["Authorization"] == "GenieKey test-api-key"


def test_alert_contains_responders_and_tags(config, payload):
    notifier = OpsGenieNotifier(config)
    with patch("cronwatch.notifiers.opsgenie_notifier.requests.post") as mock_post:
        mock_post.return_value = _mock_response(202)
        notifier.send(payload)

    body = mock_post.call_args[1]["json"]
    assert body["responders"] == [{"type": "team", "name": "platform"}]
    assert "cron" in body["tags"]


def test_details_include_last_seen(config, payload):
    notifier = OpsGenieNotifier(config)
    with patch("cronwatch.notifiers.opsgenie_notifier.requests.post") as mock_post:
        mock_post.return_value = _mock_response(202)
        notifier.send(payload)

    details = mock_post.call_args[1]["json"]["details"]
    assert "2024-01-10" in details["last_seen"]
    assert details["exit_code"] == "n/a"


def test_details_never_ran(config):
    p = AlertPayload(job_name="sync", reason="never ran", last_seen=None, exit_code=None)
    notifier = OpsGenieNotifier(config)
    with patch("cronwatch.notifiers.opsgenie_notifier.requests.post") as mock_post:
        mock_post.return_value = _mock_response(202)
        notifier.send(p)

    details = mock_post.call_args[1]["json"]["details"]
    assert details["last_seen"] == "never"


def test_http_error_is_logged_not_raised(config, payload, caplog):
    notifier = OpsGenieNotifier(config)
    with patch("cronwatch.notifiers.opsgenie_notifier.requests.post") as mock_post:
        mock_post.side_effect = requests.RequestException("connection refused")
        notifier.send(payload)  # must not raise

    assert "OpsGenie notification failed" in caplog.text
