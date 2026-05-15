"""ClickUp notifier — creates a task in a ClickUp list when a cron alert fires."""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

import requests

from cronwatch.notifiers.base import AlertPayload, BaseNotifier

logger = logging.getLogger(__name__)

_API_BASE = "https://api.clickup.com/api/v2"


@dataclass
class ClickUpConfig:
    """Configuration for the ClickUp notifier."""

    api_token: str
    list_id: str
    # Optional tag names to attach to every created task.
    tags: List[str] = field(default_factory=list)
    # ClickUp priority: 1=urgent, 2=high, 3=normal, 4=low
    priority: int = 2
    timeout: int = 10

    def __post_init__(self) -> None:
        if not self.api_token:
            raise ValueError("ClickUpConfig.api_token must not be empty")
        if not self.list_id:
            raise ValueError("ClickUpConfig.list_id must not be empty")
        if self.priority not in (1, 2, 3, 4):
            raise ValueError("ClickUpConfig.priority must be 1, 2, 3, or 4")


class ClickUpNotifier(BaseNotifier):
    """Send cronwatch alerts to ClickUp as new tasks."""

    def __init__(self, config: ClickUpConfig) -> None:
        self._config = config
        self._headers = {
            "Authorization": config.api_token,
            "Content-Type": "application/json",
        }

    def send(self, payload: AlertPayload) -> None:
        url = f"{_API_BASE}/list/{self._config.list_id}/task"
        body = self._build_task(payload)
        try:
            resp = requests.post(
                url,
                json=body,
                headers=self._headers,
                timeout=self._config.timeout,
            )
            resp.raise_for_status()
            task_id = resp.json().get("id", "<unknown>")
            logger.info("ClickUp task created: %s (job=%s)", task_id, payload.job_name)
        except requests.RequestException as exc:
            logger.error("ClickUp notification failed for job %s: %s", payload.job_name, exc)

    def _build_task(self, payload: AlertPayload) -> Dict[str, Any]:
        task: Dict[str, Any] = {
            "name": f"[cronwatch] {payload.job_name}: {payload.reason}",
            "description": payload.summary(),
            "priority": self._config.priority,
        }
        if self._config.tags:
            task["tags"] = self._config.tags
        return task
