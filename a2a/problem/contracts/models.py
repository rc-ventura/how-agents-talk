"""
Domain contracts for the incident response scenario.
 
All agents share these models — the incident is always the same:
  payments-service · 34% error rate · deploy #4821 · broken DB migration
  
  Using Pydantic v2 for:
  - automatic validation and coercion
  - .model_dump() / .model_dump_json() for A2A serialization
  - .model_json_schema() for A2A type discovery
"""

from pydantic import BaseModel, Field

from enum import Enum
from typing import Optional


class Severity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class IncidentStatus(str, Enum):
    OPEN = "open"
    INVESTIGATING = "investigating"
    REMEDIATING = "remediating"
    RESOLVED = "resolved"


class Alert(BaseModel):
    service: str
    error_rate: float
    deploy_id: str
    timestamp: str
    region: str
    severity: Severity = Severity.HIGH

    def summary(self) -> str:
        return f"{self.service} · {self.error_rate}% error rate · deploy {self.deploy_id} · {self.region}"


class TriageResult(BaseModel):
    alert: Alert
    priority: Severity
    category: str
    suspected_cause: str
    recommended_next_steps: str
    confidence: float = Field(ge=0.0, le=1.0)


class InvestigationResult(BaseModel):
    alert: Alert
    root_cause: str
    evidence: list[str]
    affected_components: list[str]
    timeline: list[str]
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)


class RemediationPlan(BaseModel):
    alert:                       Alert
    action:                      str
    target:                      str
    steps:                       list[str] = []
    estimated_recovery_minutes:  int = 0
    executed:                    bool = False
    result:                      Optional[str] = None
 
 
class IncidentReport(BaseModel):
    alert:              Alert
    status:             IncidentStatus
    triage:             Optional[TriageResult] = None
    investigation:      Optional[InvestigationResult] = None
    remediation:        Optional[RemediationPlan] = None
    resolution_summary: Optional[str] = None
    resolved_at:        Optional[str] = None
    duration_minutes:   Optional[int] = None