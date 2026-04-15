import sys
from pathlib import Path
from datetime import datetime, timezone

sys.path.insert(0, str(Path(__file__).parents[3]))

from problem.mocks.data import STAKEHOLDERS


class MockNotifications:
    """
    Mock notifications adapter for testing
    """
    def notify(self, service: str, message: str,
               severity: str = "high", channel: str = "team") -> dict:
        """
        Send a notification to the appropriate channel
        
        Args:
            service: Name of the service
            message: Notification message
            severity: Severity level (high, critical)
            channel: Channel to send the notification (team, escalation)
            
        Returns:
            Dictionary with notification details
        """
        targets = STAKEHOLDERS.get(service)
        if targets is None:
            return {"error": f"No stakeholder config for '{service}'"}
        if severity == "critical" or channel == "escalation":
            destination   = targets["escalation_channel"]
            also_notified = [targets["oncall_engineer"], targets["manager"]]
        else:
            destination   = targets["team_channel"]
            also_notified = [targets["oncall_engineer"]]
        return {
            "notified":        True,
            "channel":         destination,
            "also_paged":      also_notified,
            "severity":        severity,
            "message_preview": message[:120],
            "sent_at":         datetime.now(timezone.utc).isoformat(),
        }

    def create_report(self, service: str, summary: str, root_cause: str,
                      action_taken: str, status: str = "resolved") -> dict:
        """
        Create an incident report
        
        Args:
            service: Name of the service
            summary: Summary of the incident
            root_cause: Root cause of the incident
            action_taken: Actions taken to resolve the incident
            status: Status of the incident (resolved, in_progress, etc.)
            
        Returns:
            Dictionary with report details
        """
        report_id = f"INC-{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M')}"
        return {
            "report_id":  report_id,
            "service":    service,
            "status":     status,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "report": {
                "summary":      summary,
                "root_cause":   root_cause,
                "action_taken": action_taken,
            },
        }