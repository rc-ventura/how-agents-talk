
"""
Composition root — returns mock adapters for all ports.

To swap for real integrations, replace the return value in each function:
  resolve_metrics()       → DatadogMetrics  (needs DD_API_KEY, DD_APP_KEY)
  resolve_logs()          → DatadogLogs     (needs DD_API_KEY, DD_APP_KEY)
  resolve_notifications() → PagerDutyNotifications (needs PD_API_KEY, PD_SERVICE_ID)
"""

from ports.metrics       import MetricsPort
from ports.logs          import LogsPort
from ports.deployments   import DeploymentsPort
from ports.notifications import NotificationsPort

from adapters.mock.metrics       import MockMetrics
from adapters.mock.logs          import MockLogs
from adapters.mock.deployments   import MockDeployments
from adapters.mock.notifications import MockNotifications


def resolve_metrics() -> MetricsPort:
    """Resolve metrics adapter."""
    return MockMetrics()

def resolve_logs() -> LogsPort:
    """Resolve logs adapter."""
    return MockLogs()

def resolve_notifications() -> NotificationsPort:
    """Resolve notifications adapter."""
    return MockNotifications()  

def resolve_deployments() -> DeploymentsPort:
    """Resolve deployments adapter."""
    return MockDeployments()

