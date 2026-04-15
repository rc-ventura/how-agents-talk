"""
MCP Server — incident-response-mcp
 
Standard: FastMCP standalone + ports & adapters.
As tools delegate to adapters resolved in deps.py.
Switch from mock to Datadog/PagerDuty: just change env vars, no need to touch here.
 
Run with mocks (default):
    fastmcp run server.py --transport http --port 8000
 
Run with real adapters:
    METRICS_ADAPTER=datadog LOGS_ADAPTER=datadog \\
    NOTIFICATIONS_ADAPTER=pagerduty \\
    DD_API_KEY=... DD_APP_KEY=... PD_API_KEY=... PD_SERVICE_ID=... PD_FROM_EMAIL=... \\
    fastmcp run server.py --transport http --port 8000
"""


import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[2]))

from mcp import FastMCP
from deps import resolve_metrics, resolve_logs, resolve_deployments, resolve_notifications
from problem.mocks.data import AGENT_CARDS

# ===== Instances =============================

mcp = FastMCP(
    "incident-response-mcp",
    instructions=(
        "MCP server for incident response operations. "
        "Use query_metrics / get_error_rate to check service health,"
        "query_logs to find error patterns, get_deployment_info to inspect"
        "recent deploys, execute_rollback to remediate"
        "notify_team to alert stakeholders"
        "create_incident_report to document the resolution"
    ),
)

# ===== Adapters resolutions ==================

_metrics       = resolve_metrics()
_logs          = resolve_logs()
_deployments   = resolve_deployments()
_notifications = resolve_notifications()

# === TOOLS ==================================

@mcp.tool()
def query_metrics(service: str) -> dict:
    """
    Return current operational metrics for a service.
 
    Args:
        service: Service name, e.g. "payments-service"
    """

    return _metrics.get_metrics(service)


@mcp.tool()
def get_error_rate(service: str) -> dict:
    """
    Return current error rate for a service.
 
    Args:
        service: Service name, e.g. "payments-service"
    """

    return _metrics.get_error_rate(service)

@mcp.tool()
def query_logs(service: str, level: str = "ERROR", limit: int = 20) -> dict:
    """
    Retrieve recent log entries for a service, filtered by level.
 
    Args:
        service: Service name, e.g. "payments-service"
        level:   ERROR | WARN | INFO | ALL  (default: ERROR)
        limit:   Max entries to return       (default: 20)
    """    
    return _logs.query_logs(service, level, limit)


@mcp.tool()
def get_deployment_info(service: str, deploy_id: str = "latest") -> dict:
    """
    Return deployment details for a service, including applied migrations.
 
    Args:
        service:   Service name, e.g. "payments-service"
        deploy_id: Specific ID (e.g. "#4821") or "latest" (default)
    """
    return _deployments.get_deployment_info(service, deploy_id)

@mcp.tool()
def execute_rollback(service: str, deploy_id: str) -> dict:
    """
    Execute a rollback for a deployment to the previous stable version.
 
    Args:
        service:   Service name, e.g. "payments-service"
        deploy_id: Deploy to roll back, e.g. "#4821"
    """  
    return _deployments.execute_rollback(service, deploy_id)

@mcp.tool()
def notify_team(
    service: str,
    message: str,
    severity: str = "high",
    channel: str = "team"
) -> dict:
    """
    Send an incident notification to the appropriate team or escalation channel.
 
    Args:
        service:  Service name, e.g. "payments-service"
        message:  Notification body
        severity: low | medium | high | critical  (critical auto-escalates)
        channel:  slack | discord                 (default: slack)
    """    
    return _notifications.notify(service, message, severity, channel)

@mcp.tool()
def create_incident_report(
    service: str,
    summary: str,
    root_cause: str,
    action_taken: str,
    status: str = "resolved",
) -> dict:
    """
    Create a structured incident report after resolution.
 
    Args:
        service:      Affected service name
        summary:      One-sentence incident summary
        root_cause:   Root cause identified during investigation
        action_taken: Remediation that resolved the incident
        status:       resolved | monitoring  (default: resolved)
    """
    return _notifications.create_report(service, summary, root_cause, action_taken, status)

# ======== RESOURCES ======================

@mcp.resource("agents://cards/list", mime_type="application/json")
def list_agent_cards() -> str:
    """
    Retrieve a list of agent cards and their A2A capabilities.
 
    Returns:
        List of agent cards with their capabilities
    """
    return json.dumps({
        "agents": list(AGENT_CARDS.keys()),
        "cards": AGENT_CARDS,
    })

@mcp.resource("agents://cards/{agent_name}", mime_type="application/json")
def get_agent_card(agent_name: str) -> str:
    """
    Retrieve a specific agent card by name.
 
    Args:
        agent_name: Agent name, e.g. "agent-001"
    """
    card = AGENT_CARDS.get(agent_name)
    if card is None:
        return json.dumps({"error": f"Agent '{agent_name}' not found"})
    return json.dumps(card)


if __name__ == "__main__":
    mcp.run(transport="http")