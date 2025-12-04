"""Lightweight Jira client for fetching tickets and posting comments."""

import asyncio
import os
from typing import Optional

from src.orchestration.context import TicketInfo

try:
    import requests  # type: ignore

    REQUESTS_AVAILABLE = True
except ImportError:  # pragma: no cover - handled in code
    REQUESTS_AVAILABLE = False


class JiraClient:
    """Minimal Jira client focused on fetching ticket details."""

    def __init__(
        self,
        base_url: Optional[str] = None,
        email: Optional[str] = None,
        api_token: Optional[str] = None,
        project_key: Optional[str] = None,
    ):
        self.base_url = (base_url or "").rstrip("/")
        self.email = email or os.getenv("JIRA_EMAIL")
        self.api_token = api_token or os.getenv("JIRA_API_TOKEN")
        self.project_key = project_key

        self.enabled = bool(self.base_url and self.email and self.api_token and REQUESTS_AVAILABLE)

    async def fetch_ticket(self, ticket_id: str) -> TicketInfo:
        """Fetch Jira ticket details; falls back to stubbed data if not configured."""
        if not self.enabled:
            return self._stub_ticket(ticket_id)

        return await asyncio.to_thread(self._fetch_ticket_sync, ticket_id)

    async def add_comment(self, ticket_id: str, comment: str) -> bool:
        """Add a comment to a Jira ticket."""
        if not self.enabled:
            return False
        return await asyncio.to_thread(self._add_comment_sync, ticket_id, comment)

    def _fetch_ticket_sync(self, ticket_id: str) -> TicketInfo:
        url = f"{self.base_url}/rest/api/3/issue/{ticket_id}"
        auth = (self.email, self.api_token)
        headers = {"Accept": "application/json"}

        response = requests.get(url, auth=auth, headers=headers, timeout=10)
        response.raise_for_status()

        data = response.json()
        fields = data.get("fields", {})

        title = fields.get("summary", f"Ticket {ticket_id}")
        description = self._extract_text(fields.get("description", ""))
        acceptance_criteria = self._extract_text(fields.get("acceptance", "")) or self._extract_text(
            fields.get("customfield_acceptance", "")
        )

        return TicketInfo(
            ticket_id=ticket_id,
            title=title,
            description=description,
            acceptance_criteria=acceptance_criteria or "Not provided",
            raw_data=data,
        )

    def _add_comment_sync(self, ticket_id: str, comment: str) -> bool:
        url = f"{self.base_url}/rest/api/3/issue/{ticket_id}/comment"
        auth = (self.email, self.api_token)
        headers = {"Accept": "application/json"}
        payload = {"body": comment}

        response = requests.post(url, json=payload, auth=auth, headers=headers, timeout=10)
        return response.status_code in (200, 201)

    def _stub_ticket(self, ticket_id: str) -> TicketInfo:
        """Return stubbed ticket data when Jira is not configured."""

        # Special demo ticket for showcasing workflow
        if ticket_id == "DEMO-001":
            return TicketInfo(
                ticket_id="DEMO-001",
                title="Add input validation to config loader",
                description="""The config.py module currently loads YAML configuration without
validating required fields or types. Add validation to prevent runtime errors
from misconfigured files.

The load_config() function should validate:
- test_command must be a non-empty string
- max_retries must be an integer >= 0

This will make the system more robust and provide better error messages.""",
                acceptance_criteria="""1. Validate that test_command is a non-empty string
2. Validate that max_retries is an integer >= 0
3. Raise ConfigValidationError with descriptive message if validation fails
4. Add unit tests for validation logic""",
                raw_data={"stub": True, "demo": True, "target": "src/config.py"},
            )

        # Generic stub for other tickets
        return TicketInfo(
            ticket_id=ticket_id,
            title=f"[STUB] Implement feature for ticket {ticket_id}",
            description="Stub Jira client is not configured. Replace with real Jira credentials to fetch live data.",
            acceptance_criteria="1. Implement feature\n2. Add tests\n3. Keep code clean",
            raw_data={"stub": True},
        )

    def _extract_text(self, value) -> str:
        """Best-effort extraction of human-readable text from Jira fields."""
        if value is None:
            return ""
        if isinstance(value, str):
            return value
        # Fall back to string conversion for rich text structures
        return str(value)
