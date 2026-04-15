import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[3]))

from problem.mocks.data import LOGS

class MockLogs:
    def query_logs(self, service: str, level: str = "ERROR", limit: int = 20) -> dict:
        """
        Query logs for a specific service and deployment
        
        Args:
            service: Name of the service
            level: Log level to filter (ERROR, WARNING, INFO, DEBUG, ALL)
            limit: Maximum number of log entries to return
            
        Returns:
            Dictionary with logs or error message
        """
        entries = LOGS.get(service, [])
        
        if level.upper() != "ALL":
            entries = [entry for entry in entries if entry["level"] == level.upper()]
        return {
            "service": service,
            "level_filter": level.upper(),
            "count": len(entries[:limit]),
            "entries": entries[:limit]
        }