"""Notifications port — defines the contract for notification operations."""

from typing import Protocol


class NotificationsPort(Protocol):
    """Protocol defining notification operations."""

    def notify(
        self,
        service: str,
        message: str,
        severity: str,
        channel: str
    ) -> dict:
        """Send an incident notification to the appropriate team or escalation channel."""
        ...

    def create_report(
        self,
        service: str,
        summary: str,
        root_cause: str,
        action_taken: str,
        status: str
    ) -> dict:
        """Create a structured incident report after resolution."""
        ...
