# Notifiers

Cronwatch ships with several built-in notifiers. Each notifier implements
`BaseNotifier.send(payload: AlertPayload)` and can be passed to `CronChecker`.

## Built-in notifiers

| Notifier | Module | Extra dependency |
|---|---|---|
| `LogNotifier` | `cronwatch.notifiers.log_notifier` | — |
| `WebhookNotifier` | `cronwatch.notifiers.webhook_notifier` | `requests` |
| `EmailNotifier` | `cronwatch.notifiers.email_notifier` | — |
| `SlackNotifier` | `cronwatch.notifiers.slack_notifier` | `requests` |
| `PagerDutyNotifier` | `cronwatch.notifiers.pagerduty_notifier` | `requests` |
| `OpsGenieNotifier` | `cronwatch.notifiers.opsgenie_notifier` | `requests` |
| `VictorOpsNotifier` | `cronwatch.notifiers.victorops_notifier` | `requests` |
| `SNSNotifier` | `cronwatch.notifiers.sns_notifier` | `boto3` |

## SNSNotifier

Publishes alerts to an **AWS SNS topic** as a JSON message.

```python
from cronwatch.notifiers.sns_notifier import SNSConfig, SNSNotifier

config = SNSConfig(
    topic_arn="arn:aws:sns:us-east-1:123456789012:cronwatch-alerts",
    region_name="us-east-1",
    # Omit keys to use the default boto3 credential chain (env vars, IAM role, etc.)
    aws_access_key_id="AKIA...",
    aws_secret_access_key="...",
    subject_prefix="[cronwatch]",  # optional
)

notifier = SNSNotifier(config)
```

The SNS message body is a JSON object with the following fields:

```json
{
  "job_name": "nightly-backup",
  "reason": "missed schedule",
  "summary": "[cronwatch] nightly-backup – missed schedule",
  "last_seen": "2024-01-10T02:00:00+00:00"
}
```

`exit_code` is included when the job exited with a non-zero status.

## Writing a custom notifier

Subclass `BaseNotifier` and implement `send`:

```python
from cronwatch.notifiers.base import AlertPayload, BaseNotifier

class MyNotifier(BaseNotifier):
    def send(self, payload: AlertPayload) -> None:
        print(payload.summary())
```

Pass an instance to `CronChecker`:

```python
checker = CronChecker(registry, notifiers=[MyNotifier()])
```
