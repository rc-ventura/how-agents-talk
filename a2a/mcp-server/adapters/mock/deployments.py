import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[3]))

from problem.mocks.data import DEPLOYMENTS, ROLLBACK_OUTCOMES


class MockDeployments:
    """
    Mock deployments adapter for testing
    """

    def get_deployment_info(self, service: str, deploy_id: str = "latest") -> dict:
        """
        Get deployment information for a specific service
        
        Args:
            service: Name of the service
            deploy_id: ID of the deployment (default: "latest")
            
        Returns:
            Dictionary with deployment information or error message
        """

        deploys = DEPLOYMENTS.get(service, [])
        if not deploys:
            return {"error": f"No deployments found for '{service}'"}
        if deploy_id == "latest":
            deploy = deploys[0]
        else:
            deploy = next((d for d in deploys if d["deploy_id"] == deploy_id), None)
            if deploy is None:
                return {"error": f"Deploy '{deploy_id}' not found for '{service}'"}
        return {"service": service, "deployment": deploy}

    def execute_rollback(self, service: str, deploy_id: str) -> dict:
        """
        Execute a rollback for a specific deployment
        
        Args:
            service: Name of the service
            deploy_id: ID of the deployment to rollback
            
        Returns:
            Dictionary with rollback outcome or error message
        """
        
        outcome = ROLLBACK_OUTCOMES.get(deploy_id)
        if outcome is None:
            return {"success": False, "error": f"No rollback config for '{deploy_id}'"}
        return {"service": service, "rolled_back_deploy": deploy_id, **outcome}