"""
Mock system state for the incident scenario.

All tool implementations pull from here so every agent sees
consistent, realistic data without real infrastructure.

Scenario
--------
  payments-service was operating normally until deploy #4821 landed
  at 02:47 UTC. A DB migration script renamed column `user_id` to
  `customer_id` in the transactions table but the application code
  wasn't updated. By 02:51 the error rate had climbed to 34%.
"""

from datetime import datetime, timezone

# ─── Metrics ───────────────────────────────────────────────────────────────

METRICS = {
    "payments-service": {
        "error_rate_current": 0.34,
        "error_rate_baseline": 0.008,
        "p99_latency_ms": 4820,
        "p50_latency_ms": 1240,
        "requests_per_minute": 1850,
        "failed_requests_per_minute": 629,
        "cpu_percent": 71,
        "memory_percent": 68,
    },
    "auth-service": {
        "error_rate_current": 0.003,
        "error_rate_baseline": 0.002,
        "p99_latency_ms": 95,
        "p50_latency_ms": 22,
    },
    "api-gateway": {
        "error_rate_current": 0.011,
        "error_rate_baseline": 0.005,
        "p99_latency_ms": 210,
        "p50_latency_ms": 48,
    },
}

# ─── Logs ──────────────────────────────────────────────────────────────────

LOGS = {
    "payments-service": [
        {
            "timestamp": "2024-01-15T02:51:03Z",
            "level": "ERROR",
            "message": 'column "user_id" does not exist',
            "trace": "psycopg2.errors.UndefinedColumn: column user_id of relation transactions does not exist",
            "count": 412,
        },
        {
            "timestamp": "2024-01-15T02:51:01Z",
            "level": "ERROR",
            "message": "Database query failed: column not found",
            "trace": "sqlalchemy.exc.ProgrammingError: (psycopg2.errors.UndefinedColumn)",
            "count": 389,
        },
        {
            "timestamp": "2024-01-15T02:50:58Z",
            "level": "WARN",
            "message": "High error rate detected, alerting on-call",
            "count": 1,
        },
        {
            "timestamp": "2024-01-15T02:47:22Z",
            "level": "INFO",
            "message": "Deploy #4821 completed — migrations applied",
            "count": 1,
        },
        {
            "timestamp": "2024-01-15T02:30:00Z",
            "level": "INFO",
            "message": "Health check passed — all systems nominal",
            "count": 1,
        },
    ]
}

# ─── Deployments ───────────────────────────────────────────────────────────

DEPLOYMENTS = {
    "payments-service": [
        {
            "deploy_id": "#4821",
            "service": "payments-service",
            "version": "v2.14.1",
            "deployed_at": "2024-01-15T02:47:00Z",
            "deployed_by": "ci-pipeline",
            "status": "active",
            "region": "us-east-1",
            "migrations": [
                {
                    "name": "0042_rename_user_id_to_customer_id",
                    "status": "applied",
                    "description": "Renamed transactions.user_id → transactions.customer_id",
                }
            ],
            "previous_deploy_id": "#4820",
        },
        {
            "deploy_id": "#4820",
            "service": "payments-service",
            "version": "v2.14.0",
            "deployed_at": "2024-01-14T18:15:00Z",
            "deployed_by": "ci-pipeline",
            "status": "inactive",
            "region": "us-east-1",
            "migrations": [],
        },
    ]
}

# ─── Rollback capability ────────────────────────────────────────────────────

ROLLBACK_OUTCOMES = {
    "#4821": {
        "success": True,
        "rolled_back_to": "#4820",
        "duration_seconds": 42,
        "post_rollback_error_rate": 0.009,
        "message": "Rollback to v2.14.0 successful. Migration 0042 reversed.",
    }
}

# ─── Agent Cards ───────────────────────────────────────────────────────────

AGENT_CARDS = {
    "triage-agent": {
        "name": "Triage Agent",
        "description": "Classifies incidents by severity and category, identifies suspected cause, and recommends next steps.",
        "url": "http://localhost:8002",
        "version": "1.0.0",
        "framework": "LangGraph",
        "skills": [{
            "id": "triage_incident",
            "name": "triage_incident",
            "description": "Analyse an alert and produce a structured triage result.",
            "tags": ["incident", "triage", "classification", "priority"],
            "examples": ["Triage this alert: payments-service 34% error rate, deploy #4821"],
        }],
    },
    "investigation-agent": {
        "name": "Investigation Agent",
        "description": "Performs deep root-cause analysis using metrics, logs, and deployment data.",
        "url": "http://localhost:8003",
        "version": "1.0.0",
        "framework": "Google ADK",
        "skills": [{
            "id": "investigate_incident",
            "name": "investigate_incident",
            "description": "Correlate metrics, logs, and recent deployments to identify the root cause.",
            "tags": ["investigation", "root-cause", "logs", "metrics"],
            "examples": ["Investigate high error rate on payments-service after deploy #4821"],
        }],
    },
    "remediation-agent": {
        "name": "Remediation Agent",
        "description": "Proposes and executes remediation actions such as rollbacks, hotfixes, or scaling.",
        "url": "http://localhost:8004",
        "version": "1.0.0",
        "framework": "OpenAI SDK",
        "skills": [{
            "id": "remediate_incident",
            "name": "remediate_incident",
            "description": "Given a root cause, determine the safest remediation action and execute it.",
            "tags": ["remediation", "rollback", "hotfix", "recovery"],
            "examples": ["Rollback deploy #4821 on payments-service"],
        }],
    },
    "communication-agent": {
        "name": "Communication Agent",
        "description": "Notifies stakeholders and produces structured incident reports.",
        "url": "http://localhost:8005",
        "version": "1.0.0",
        "framework": "CrewAI",
        "skills": [{
            "id": "communicate_incident",
            "name": "communicate_incident",
            "description": "Send stakeholder notifications and produce a full incident report.",
            "tags": ["communication", "notification", "report", "postmortem"],
            "examples": ["Notify team about payments-service incident and create report"],
        }],
    },
}

# ─── Notification targets ───────────────────────────────────────────────────

STAKEHOLDERS = {
    "payments-service": {
        "oncall_engineer": "alice@company.com",
        "team_channel": "#payments-oncall",
        "escalation_channel": "#incidents-critical",
        "manager": "bob@company.com",
    }
}