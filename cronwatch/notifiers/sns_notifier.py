"""AWS SNS notifier for cronwatch alerts."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import List, Optional

try:
    import boto3
    from botocore.exceptions import BotoCoreError, ClientError
except ImportError:  # pragma: no cover
    boto3 = None  # type: ignore

from cronwatch.notifiers.base import AlertPayload, BaseNotifier


@dataclass
class SNSConfig:
    topic_arn: str
    region_name: str = "us-east-1"
    aws_access_key_id: Optional[str] = None
    aws_secret_access_key: Optional[str] = None
    subject_prefix: str = "[cronwatch]"
    extra_attributes: dict = field(default_factory=dict)


class SNSNotifier(BaseNotifier):
    """Sends cronwatch alerts to an AWS SNS topic."""

    def __init__(self, config: SNSConfig) -> None:
        if boto3 is None:  # pragma: no cover
            raise ImportError("boto3 is required for SNSNotifier: pip install boto3")
        self.config = config
        self._client = boto3.client(
            "sns",
            region_name=config.region_name,
            aws_access_key_id=config.aws_access_key_id,
            aws_secret_access_key=config.aws_secret_access_key,
        )

    def send(self, payload: AlertPayload) -> None:
        subject = f"{self.config.subject_prefix} {payload.job_name} – {payload.reason}"
        # SNS subjects are limited to 100 characters
        subject = subject[:100]

        message = self._build_message(payload)

        try:
            self._client.publish(
                TopicArn=self.config.topic_arn,
                Subject=subject,
                Message=message,
            )
        except (BotoCoreError, ClientError) as exc:
            raise RuntimeError(f"SNS publish failed: {exc}") from exc

    def _build_message(self, payload: AlertPayload) -> str:
        data = {
            "job_name": payload.job_name,
            "reason": payload.reason,
            "summary": payload.summary(),
        }
        if payload.last_seen is not None:
            data["last_seen"] = payload.last_seen.isoformat()
        if payload.exit_code is not None:
            data["exit_code"] = payload.exit_code
        return json.dumps(data, indent=2)
