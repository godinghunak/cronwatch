# Cronwatch Notifiers

Cronwatch ships with several built-in notifiers. Each implements `BaseNotifier`
and can be passed to `CronChecker`.

## Available Notifiers

| Notifier | Class | Config |
|---|---|---|
| Log (stdout) | `LogNotifier` | — |
| Webhook | `WebhookNotifier` | — |
| Email (SMTP) | `EmailNotifier` | `EmailConfig` |
| Slack | `SlackNotifier` | `SlackConfig` |
| PagerDuty | `PagerDutyNotifier` | `PagerDutyConfig` |
| OpsGenie | `OpsGenieNotifier` | `OpsGenieConfig` |
| VictorOps | `VictorOpsNotifier` | `VictorOpsConfig` |

## VictorOps (Splunk On-Call)

Uses the VictorOps **REST Endpoint** integration.

```python
from cronwatch.notifiers import VictorOpsConfig, VictorOpsNotifier

config = VictorOpsConfig(
    routing_key="db-team",
    rest_endpoint="https://alert.victorops.com/integrations/generic/<ID>/alert",
    timeout=10,
    extra_fields={"env": "production"},
)
notifier = VictorOpsNotifier(config)
```

The `routing_key` is appended to the `rest_endpoint` URL automatically.
Optional `extra_fields` are merged into the alert body.

## Writing a Custom Notifier

Subclass `BaseNotifier` and implement `send`:

```python
from cronwatch.notifiers.base import AlertPayload, BaseNotifier

class MyNotifier(BaseNotifier):
    def send(self, payload: AlertPayload) -> None:
        print(payload.summary())
```

Pass an instance to `CronChecker`:

```python
from cronwatch.checker import CronChecker

checker = CronChecker(registry, notifiers=[MyNotifier()])
checker.check_all()
```
