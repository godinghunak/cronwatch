# Cronwatch Notifiers

Cronwatch ships with several built-in notifiers. Each notifier implements
`BaseNotifier.send(payload: AlertPayload)` and must never raise on delivery
failure — errors are logged instead.

## Available Notifiers

| Notifier | Class | Config dataclass |
|---|---|---|
| Structured log | `LogNotifier` | *(none)* |
| Generic webhook | `WebhookNotifier` | `WebhookNotifier(url, ...)` |
| Email (SMTP) | `EmailNotifier` | `EmailConfig` |
| Slack | `SlackNotifier` | `SlackConfig` |
| PagerDuty | `PagerDutyNotifier` | `PagerDutyConfig` |
| OpsGenie | `OpsGenieNotifier` | `OpsGenieConfig` |

## OpsGenie

```python
from cronwatch.notifiers.opsgenie_notifier import OpsGenieConfig, OpsGenieNotifier

config = OpsGenieConfig(
    api_key="YOUR_OPSGENIE_API_KEY",
    responders=[{"type": "team", "name": "platform-ops"}],
    tags=["cron", "production"],
    priority="P2",   # P1 (critical) – P5 (informational)
)
notifier = OpsGenieNotifier(config)
```

Alerts are sent to `https://api.opsgenie.com/v2/alerts`. The alert `alias` is
set to `cronwatch-<job_name>` so repeated firings de-duplicate in OpsGenie.

### OpsGenieConfig fields

| Field | Type | Default | Description |
|---|---|---|---|
| `api_key` | `str` | *required* | OpsGenie API integration key |
| `responders` | `list[dict]` | `[]` | Teams / users to notify |
| `tags` | `list[str]` | `[]` | Tags attached to the alert |
| `priority` | `str` | `"P3"` | OpsGenie priority (P1–P5) |
| `timeout` | `int` | `10` | HTTP request timeout in seconds |

## Adding a custom notifier

```python
from cronwatch.notifiers.base import AlertPayload, BaseNotifier

class MyNotifier(BaseNotifier):
    def send(self, payload: AlertPayload) -> None:
        # deliver the alert; catch all exceptions internally
        ...
```

Register it with `CronChecker` by appending to its `notifiers` list.
