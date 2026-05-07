"""Tests for VictorOpsNotifier."""

from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest
import requests

from cronwatch.notifiers.base import AlertPayload
from cronwatch.notifiers.victorops_notifier import VictorOpsConfig, VictorOpsNotifier


def _utc(*args: int) -> datetime:
    return datetime(*args, tzinfo=timezone.utc)


@pytest.fixture()
def config() -> VictorOpsConfig:
    return VictorOpsConfig(
        routing_key="db-team",
        rest_endpoint="https://alert.victorops.com/integrations/generic/12345/alert",
    )


@pytest.fixture()
def payload() -> AlertPayload:
    return AlertPayload(
        job_name="nightly-backup",
        reason="missed schedule",
        last_seen=_utc(2024, 1, 15, 3, 0, 0),
    )


def _mock_response(status_code: int = 200) -> MagicMock:
    resp = MagicMock()
    resp.status_code = status_code
    resp.raise_for_status = MagicMock()
    if status_code >= 400:
        resp.raise_for_status.side_effect = requests.HTTPError(response=resp)
    return resp


def test_send_posts_to_correct_url(config: VictorOpsConfig, payload: AlertPayload) -> None:
    with patch("cronwatch.notifiers.victorops_notifier.requests.post") as mock_post:
        mock_post.return_value = _mock_response(200)
        notifier = VictorOpsNotifier(config)
        notifier.send(payload)

    mock_post.assert_called_once()
    url = mock_post.call_args[0][0]
    assert "db-team" in url
    assert "alert.victorops.com" in url


def test_send_includes_job_name_in_body(config: VictorOpsConfig, payload: AlertPayload) -> None:
    with patch("cronwatch.notifiers.victorops_notifier.requests.post") as mock_post:
        mock_post.return_value = _mock_response(200)
        VictorOpsNotifier(config).send(payload)

    body = mock_post.call_args[1]["json"]
    assert body["job_name"] == "nightly-backup"
    assert body["message_type"] == "CRITICAL"
    assert "nightly-backup" in body["entity_id"]


def test_send_includes_last_seen_when_present(config: VictorOpsConfig, payload: AlertPayload) -> None:
    with patch("cronwatch.notifiers.victorops_notifier.requests.post") as mock_post:
        mock_post.return_value = _mock_response(200)
        VictorOpsNotifier(config).send(payload)

    body = mock_post.call_args[1]["json"]
    assert "last_seen" in body
    assert "2024-01-15" in body["last_seen"]


def test_send_omits_last_seen_when_none(config: VictorOpsConfig) -> None:
    p = AlertPayload(job_name="job", reason="never ran", last_seen=None)
    with patch("cronwatch.notifiers.victorops_notifier.requests.post") as mock_post:
        mock_post.return_value = _mock_response(200)
        VictorOpsNotifier(config).send(p)

    body = mock_post.call_args[1]["json"]
    assert "last_seen" not in body


def test_extra_fields_merged_into_body(payload: AlertPayload) -> None:
    cfg = VictorOpsConfig(
        routing_key="ops",
        rest_endpoint="https://alert.victorops.com/integrations/generic/99/alert",
        extra_fields={"team": "platform", "env": "prod"},
    )
    with patch("cronwatch.notifiers.victorops_notifier.requests.post") as mock_post:
        mock_post.return_value = _mock_response(200)
        VictorOpsNotifier(cfg).send(payload)

    body = mock_post.call_args[1]["json"]
    assert body["team"] == "platform"
    assert body["env"] == "prod"


def test_request_exception_is_logged_not_raised(config: VictorOpsConfig, payload: AlertPayload) -> None:
    with patch("cronwatch.notifiers.victorops_notifier.requests.post") as mock_post:
        mock_post.side_effect = requests.ConnectionError("unreachable")
        notifier = VictorOpsNotifier(config)
        notifier.send(payload)  # must not raise
