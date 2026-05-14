# Splunk Notifier

The `SplunkNotifier` sends cronwatch alerts to a **Splunk HTTP Event Collector (HEC)** endpoint.

## Prerequisites

1. Enable the HEC input in your Splunk instance.
2. Create a HEC token with write access to the desired index.

## Configuration

```python
from cronwatch.notifiers.splunk_notifier import SplunkConfig, SplunkNotifier

config = SplunkConfig(
    hec_url="https://splunk.example.com:8088/services/collector/event",
    token="YOUR-HEC-TOKEN",
    index="cronwatch",          # optional; uses Splunk default when omitted
    source="cronwatch",         # default
    sourcetype="cronwatch:alert",  # default
    timeout=10,                 # seconds
    verify_ssl=True,            # set False only in dev/test
    extra_fields={"env": "production"},  # merged into each event body
)

notifier = SplunkNotifier(config)
```

## Event Schema

Each HEC event has the following shape:

```json
{
  "time": 1704844800.0,
  "source": "cronwatch",
  "sourcetype": "cronwatch:alert",
  "index": "cronwatch",
  "event": {
    "job": "nightly-backup",
    "reason": "missed_schedule",
    "summary": "[cronwatch] nightly-backup — missed_schedule",
    "last_seen": "2024-01-10T02:00:00+00:00",
    "consecutive_failures": 0,
    "env": "production"
  }
}
```

## SSL Verification

For self-signed certificates in internal Splunk deployments set `verify_ssl=False`.
Never disable SSL verification in production against a public endpoint.
