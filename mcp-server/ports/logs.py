"""Logs port — defines the contract for log operations."""

from typing import Protocol


class LogsPort(Protocol):
    """Protocol defining logs operations."""

    def query_logs(self, service: str, level: str, limit: int) -> dict:
        """Retrieve recent log entries for a service, filtered by level."""
        ...
