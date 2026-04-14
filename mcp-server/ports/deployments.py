"""Deployments port — defines the contract for deployment operations."""

from typing import Protocol


class DeploymentsPort(Protocol):
    """Protocol defining deployment operations."""

    def get_deployment_info(self, service: str, deploy_id: str) -> dict:
        """Return deployment details for a service, including applied migrations."""
        ...

    def execute_rollback(self, service: str, deploy_id: str) -> dict:
        """Execute a rollback for a deployment to the previous stable version."""
        ...
