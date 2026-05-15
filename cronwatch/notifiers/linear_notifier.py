"""Linear issue notifier for cronwatch alerts."""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Optional

import requests

from cronwatch.notifiers.base import AlertPayload, BaseNotifier

logger = logging.getLogger(__name__)

_LINEAR_API_URL = "https://api.linear.app/graphql"


@dataclass
class LinearConfig:
    api_key: str
    team_id: str
    assignee_id: Optional[str] = None
    priority: int = 2  # 1=urgent, 2=high, 3=medium, 4=low
    label_ids: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not self.api_key:
            raise ValueError("LinearConfig.api_key must not be empty")
        if not self.team_id:
            raise ValueError("LinearConfig.team_id must not be empty")
        if self.priority not in (1, 2, 3, 4):
            raise ValueError("LinearConfig.priority must be 1, 2, 3, or 4")


class LinearNotifier(BaseNotifier):
    """Creates a Linear issue when a cron job alert fires."""

    def __init__(self, config: LinearConfig) -> None:
        self._config = config

    def send(self, payload: AlertPayload) -> None:
        mutation = """
        mutation CreateIssue($input: IssueCreateInput!) {
            issueCreate(input: $input) {
                success
                issue { id title url }
            }
        }
        """
        variables: dict = {
            "input": {
                "teamId": self._config.team_id,
                "title": f"[cronwatch] {payload.job_name}: {payload.reason}",
                "description": self._build_description(payload),
                "priority": self._config.priority,
            }
        }
        if self._config.assignee_id:
            variables["input"]["assigneeId"] = self._config.assignee_id
        if self._config.label_ids:
            variables["input"]["labelIds"] = self._config.label_ids

        headers = {
            "Authorization": self._config.api_key,
            "Content-Type": "application/json",
        }
        response = requests.post(
            _LINEAR_API_URL,
            json={"query": mutation, "variables": variables},
            headers=headers,
            timeout=10,
        )
        response.raise_for_status()
        data = response.json()
        if not data.get("data", {}).get("issueCreate", {}).get("success"):
            logger.error("Linear issue creation failed: %s", data)
            return
        issue_url = data["data"]["issueCreate"]["issue"]["url"]
        logger.info("Linear issue created: %s", issue_url)

    def _build_description(self, payload: AlertPayload) -> str:
        lines = [
            f"**Job:** `{payload.job_name}`",
            f"**Reason:** {payload.reason}",
        ]
        if payload.last_success:
            lines.append(f"**Last success:** {payload.last_success.isoformat()}")  
        if payload.last_failure:
            lines.append(f"**Last failure:** {payload.last_failure.isoformat()}")
        lines.append(f"\n_{payload.summary}_")
        return "\n".join(lines)
