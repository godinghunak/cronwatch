"""cronwatch notifier registry.

All built-in notifiers are importable from this package.  Each notifier is
loaded lazily so that missing optional dependencies (e.g. boto3) do not break
imports of unrelated notifiers.
"""

from __future__ import annotations

from importlib import import_module
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from cronwatch.notifiers.base import BaseNotifier

_NOTIFIER_MAP: dict[str, tuple[str, str]] = {
    "LogNotifier": (".log_notifier", "LogNotifier"),
    "WebhookNotifier": (".webhook_notifier", "WebhookNotifier"),
    "EmailNotifier": (".email_notifier", "EmailNotifier"),
    "SlackNotifier": (".slack_notifier", "SlackNotifier"),
    "PagerDutyNotifier": (".pagerduty_notifier", "PagerDutyNotifier"),
    "OpsGenieNotifier": (".opsgenie_notifier", "OpsGenieNotifier"),
    "VictorOpsNotifier": (".victorops_notifier", "VictorOpsNotifier"),
    "SNSNotifier": (".sns_notifier", "SNSNotifier"),
    "TeamsNotifier": (".teams_notifier", "TeamsNotifier"),
    "DiscordNotifier": (".discord_notifier", "DiscordNotifier"),
    "TelegramNotifier": (".telegram_notifier", "TelegramNotifier"),
    "DatadogNotifier": (".datadog_notifier", "DatadogNotifier"),
    "GrafanaNotifier": (".grafana_notifier", "GrafanaNotifier"),
    "MattermostNotifier": (".mattermost_notifier", "MattermostNotifier"),
    "GoogleChatNotifier": (".googlechat_notifier", "GoogleChatNotifier"),
    "SMSNotifier": (".sms_notifier", "SMSNotifier"),
    "SplunkNotifier": (".splunk_notifier", "SplunkNotifier"),
    "PushoverNotifier": (".pushover_notifier", "PushoverNotifier"),
    "ZulipNotifier": (".zulip_notifier", "ZulipNotifier"),
    "RocketChatNotifier": (".rocketchat_notifier", "RocketChatNotifier"),
}


def __getattr__(name: str) -> type[BaseNotifier]:
    if name in _NOTIFIER_MAP:
        module_path, class_name = _NOTIFIER_MAP[name]
        module = import_module(module_path, package=__name__)
        return getattr(module, class_name)  # type: ignore[return-value]
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = list(_NOTIFIER_MAP.keys())
