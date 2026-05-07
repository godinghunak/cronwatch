# Notifiers

All notifiers implement `BaseNotifier` and accept an `AlertPayload`.

## Built-in notifiers

| Notifier | Config class | Destination |
|---|---|---|
| `LogNotifier` | — | Python `logging` |
| `WebhookNotifier` | — | Generic HTTP webhook |
| `EmailNotifier` | `EmailConfig` | SMTP email |
| `SlackNotifier` | `SlackConfig` | Slack Incoming Webhook |
| `PagerDutyNotifier` | `PagerDutyConfig` | PagerDuty Events API v2 |
| `OpsGenieNotifier` | `OpsGenieConfig` | OpsGenie Alerts API |
| `VictorOpsNotifier` | `VictorOpsConfig` | VictorOps REST Endpoint |
| `SNSNotifier` | `SNSConfig` | AWS SNS topic |
| `TeamsNotifier` | `TeamsConfig` | Microsoft Teams Incoming Webhook |

## Microsoft Teams

```python
from cronwatch.notifiers.teams_notifier import TeamsConfig, TeamsNotifier

config = TeamsConfig(
    webhook_url="https://outlook.office.com/webhook/<id>/IncomingWebhook/<token>",
    mention_emails=["oncall@example.com"],  # optional
    timeout=10,
)
notifier = TeamsNotifier(config)
```

The notifier posts a **MessageCard** to the configured Incoming Webhook URL.
Optional `mention_emails` are prepended to the card text as `<at>` mentions
(note: mentions only resolve for users inside the same tenant).

## Writing a custom notifier

```python
from cronwatch.notifiers.base import AlertPayload, BaseNotifier

class MyNotifier(BaseNotifier):
    def send(self, payload: AlertPayload) -> None:
        print(payload.summary())
```

Register it with the checker:

```python
from cronwatch.checker import CronChecker

checker = CronChecker(registry, notifiers=[MyNotifier()])
```
