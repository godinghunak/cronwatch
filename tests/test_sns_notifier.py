"""Tests for SNSNotifier."""

from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest

from cronwatch.notifiers.base import AlertPayload
from cronwatch.notifiers.sns_notifier import SNSConfig, SNSNotifier


def _utc(*args) -> datetime:
    return datetime(*args, tzinfo=timezone.utc)


@pytest.fixture()
def config() -> SNSConfig:
    return SNSConfig(
        topic_arn="arn:aws:sns:us-east-1:123456789012:cronwatch-alerts",
        region_name="us-east-1",
        aws_access_key_id="AKIAIOSFODNN7EXAMPLE",
        aws_secret_access_key="secret",
    )


@pytest.fixture()
def payload() -> AlertPayload:
    return AlertPayload(
        job_name="nightly-backup",
        reason="missed schedule",
        last_seen=_utc(2024, 1, 10, 2, 0, 0),
        exit_code=None,
    )


@pytest.fixture()
def mock_boto3_client():
    with patch("cronwatch.notifiers.sns_notifier.boto3") as mock_boto3:
        mock_client = MagicMock()
        mock_boto3.client.return_value = mock_client
        yield mock_client


def test_send_publishes_to_topic(config, payload, mock_boto3_client):
    notifier = SNSNotifier(config)
    notifier.send(payload)

    mock_boto3_client.publish.assert_called_once()
    call_kwargs = mock_boto3_client.publish.call_args[1]
    assert call_kwargs["TopicArn"] == config.topic_arn


def test_subject_contains_job_name_and_reason(config, payload, mock_boto3_client):
    notifier = SNSNotifier(config)
    notifier.send(payload)

    call_kwargs = mock_boto3_client.publish.call_args[1]
    assert "nightly-backup" in call_kwargs["Subject"]
    assert "missed schedule" in call_kwargs["Subject"]


def test_subject_respects_100_char_limit(config, mock_boto3_client):
    long_payload = AlertPayload(
        job_name="x" * 80,
        reason="y" * 80,
        last_seen=None,
        exit_code=None,
    )
    notifier = SNSNotifier(config)
    notifier.send(long_payload)

    call_kwargs = mock_boto3_client.publish.call_args[1]
    assert len(call_kwargs["Subject"]) <= 100


def test_message_is_valid_json(config, payload, mock_boto3_client):
    import json

    notifier = SNSNotifier(config)
    notifier.send(payload)

    call_kwargs = mock_boto3_client.publish.call_args[1]
    parsed = json.loads(call_kwargs["Message"])
    assert parsed["job_name"] == "nightly-backup"
    assert parsed["reason"] == "missed schedule"
    assert "summary" in parsed
    assert "last_seen" in parsed


def test_client_error_raises_runtime_error(config, payload, mock_boto3_client):
    from botocore.exceptions import ClientError

    mock_boto3_client.publish.side_effect = ClientError(
        {"Error": {"Code": "AuthorizationError", "Message": "Access denied"}},
        "Publish",
    )
    notifier = SNSNotifier(config)
    with pytest.raises(RuntimeError, match="SNS publish failed"):
        notifier.send(payload)


def test_subject_prefix_is_configurable(mock_boto3_client, payload):
    cfg = SNSConfig(
        topic_arn="arn:aws:sns:us-east-1:000000000000:alerts",
        subject_prefix="[PROD]",
    )
    notifier = SNSNotifier(cfg)
    notifier.send(payload)

    call_kwargs = mock_boto3_client.publish.call_args[1]
    assert call_kwargs["Subject"].startswith("[PROD]")
