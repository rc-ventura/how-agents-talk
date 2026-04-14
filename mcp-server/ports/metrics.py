"""Metrics port — defines the contract for metrics operations."""

from typing import Protocol


class MetricsPort(Protocol):
    """Protocol defining metrics operations."""

    def get_metrics(self, service: str) -> dict:
        """Return current operational metrics for a service."""
        ...

    def get_error_rate(self, service: str) -> dict:
        """Return current error rate for a service."""
        ...
