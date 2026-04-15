import sys
from pathlib import Path
import os

sys.path.insert(0, str(Path(__file__).parents[3]))

from problem.mocks.data import METRICS


ANOMALY_THRESHOLD = float(os.getenv("ANOMALY_THRESHOLD", "3.0"))


class MockMetrics:
    def get_metrics(self, service:str) -> dict:
        """
        Get metrics for a specific service
       
        Args:
            service: Name of the service
           
        Returns:
            Dictionary with service metrics or error message
        """
        data = METRICS.get(service)
        if data is None:
            return {"error": f"No metrics found for {service}"}
        return {"service": service, "metrics": data}

    def get_error_rate(self, service: str) -> dict:
        """
        Get error rate for a specific service
        
        Args:
            service: Name of the service
            
        Returns:
            Dictionary with error rate or error message and anomaly detection
        """
        data = METRICS.get(service)
        if data is None:
            return {"error": f"No metrics found for {service}"}
        current = data["error_rate_current"]
        baseline = data["error_rate_baseline"]
        
        return {
            "service": service, 
            "current": current, 
            "baseline": baseline,
            "delta": round(current - baseline, 4),
            "is_anomalous": current > baseline * ANOMALY_THRESHOLD,
        }