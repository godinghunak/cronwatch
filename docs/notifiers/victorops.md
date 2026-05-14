# VictorOps (Splunk On-Call) Notifier

Sends alert events to VictorOps (now called Splunk On-Call) via the
[REST Endpoint integration](https://help.victorops.com/knowledge-base/rest-endpoint-integration-guide/).

## Configuration

| Field | Type | Required | Default | Description |
|---|---|---|---|---|
| `rest_endpoint_url` | `str` | ✅ | — | Base URL from the VictorOps REST Endpoint integration (without routing key) |
| `routing_key` | `str` | ✅ | — | VictorOps routing key that determines escalation policy |
| `message_type` | `str` | ❌ | `"CRITICAL"` | Severity: `CRITICAL`, `WARNING`, `INFO`, `ACKNOWLEDGEMENT`, or `RECOVERY` |
| `timeout` | `int` | ❌ | `10` | HTTP request timeout in seconds |

## Usage

```python
from cronwatch.notifiers.victorops_notifier import VictorOpsConfig, VictorOpsNotifier

config = VictorOpsConfig(
    rest_endpoint_url="https://alert.victorops.com/integrations/generic/<api_id>/alert/<api_key>",
    routing_key="database-team",
    message_type="CRITICAL",
)

notifier = VictorOpsNotifier(config)
```

Pass the notifier to `CronChecker`:

```python
from cronwatch.checker import CronChecker

checker = CronChecker(registry=registry, notifiers=[notifier])
checker.check_all()
```

## Alert Payload

Each alert includes:

- **`entity_id`** — `cronwatch/<job_name>` (used for deduplication)
- **`entity_display_name`** — Human-readable label
- **`state_message`** — Full summary from `AlertPayload.summary()`
- **`monitoring_tool`** — Always `"cronwatch"`
- **`timestamp`** — Unix epoch of when the alert was triggered
- **`details`** — `reason`, `last_seen`, and `consecutive_failures`

## Recovery Alerts

To resolve an incident in VictorOps after a job recovers, send a follow-up
alert with `message_type` set to `"RECOVERY"`. The `entity_id` must match the
original alert so VictorOps can correlate and close the incident automatically.

```python
recovery_config = VictorOpsConfig(
    rest_endpoint_url="https://alert.victorops.com/integrations/generic/<api_id>/alert/<api_key>",
    routing_key="database-team",
    message_type="RECOVERY",
)

recovery_notifier = VictorOpsNotifier(recovery_config)
```
