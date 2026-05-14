from __future__ import annotations

import json
from datetime import datetime, timezone
from io import BytesIO
from unittest.mock import MagicMock, patch

import pytest

from cronwatch.notifiers.base import AlertPayload
from cronwatch.notifiers.victorops_notifier import VictorOpsConfig, VictorOpsNotifier


def _utc(*args) -> datetime:
    return datetime(*args, tzinfo=timezone.utc)


@pytest.fixture
def config() -> VictorOpsConfig:
    return VictorOpsConfig(
        routing_key="db-team",
        rest_endpoint_url="https://alert.victorops.com/integrations/generic/abc123/alert/secret",
    )


@pytest.fixture
def payload() -> AlertPayload:
    return AlertPayload(
        job_name="nightly_backup",
        reason="missed schedule",
        triggered_at=_utc(2024, 1, 15, 3, 0, 0),
        last_seen=_utc(2024, 1, 14, 3, 0, 0),
        consecutive_failures=0,
    )


def _mock_response(status: int = 200) -> MagicMock:
    resp = MagicMock()
    resp.status = status
    resp.__enter__ = lambda s: s
    resp.__exit__ = MagicMock(return_value=False)
    return resp


def test_send_posts_to_correct_url(config, payload):
    with patch("urllib.request.urlopen", return_value=_mock_response()) as mock_open:
        notifier = VictorOpsNotifier(config)
        notifier.send(payload)
        mock_open.assert_called_once()
        req = mock_open.call_args[0][0]
        assert "db-team" in req.full_url
        assert "secret" in req.full_url


def test_send_includes_job_name_in_entity_id(config, payload):
    with patch("urllib.request.urlopen", return_value=_mock_response()):
        notifier = VictorOpsNotifier(config)
        event = notifier._build_event(payload)
        assert "nightly_backup" in event["entity_id"]


def test_send_uses_configured_message_type(payload):
    cfg = VictorOpsConfig(
        routing_key="ops",
        rest_endpoint_url="https://alert.victorops.com/integrations/generic/x/alert/y",
        message_type="WARNING",
    )
    notifier = VictorOpsNotifier(cfg)
    event = notifier._build_event(payload)
    assert event["message_type"] == "WARNING"


def test_send_logs_on_http_error(config, payload, caplog):
    import urllib.error

    with patch("urllib.request.urlopen", side_effect=urllib.error.HTTPError(
        url=None, code=500, msg="Server Error", hdrs=None, fp=None
    )):
        notifier = VictorOpsNotifier(config)
        with caplog.at_level("ERROR"):
            notifier.send(payload)  # should not raise
        assert "VictorOps HTTP error" in caplog.text


def test_build_event_last_seen_none(config):
    p = AlertPayload(
        job_name="job_x",
        reason="never ran",
        triggered_at=_utc(2024, 1, 15, 0, 0, 0),
        last_seen=None,
        consecutive_failures=0,
    )
    notifier = VictorOpsNotifier(config)
    event = notifier._build_event(p)
    assert event["details"]["last_seen"] is None


def test_build_event_consecutive_failures(config, payload):
    payload.consecutive_failures = 5
    notifier = VictorOpsNotifier(config)
    event = notifier._build_event(payload)
    assert event["details"]["consecutive_failures"] == 5
