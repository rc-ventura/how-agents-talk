"""LangGraph Studio entry-point for the Triage Agent.

This file wraps the mock MCP adapters as synchronous @tool functions so the
agent graph can be loaded by `langgraph dev` without a running MCP server.

Usage:
    cd a2a/triage-agent
    langgraph dev

The triage_graph is identical to the runtime agent (same SYSTEM_PROMPT,
TriageResult schema and tools) — only the tool transport changes
(in-process mocks instead of HTTP MCP).
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

# ── make mock adapters importable ────────────────────────────────────────
# The MCP server code lives in a2a/mcp-server; we temporarily inject it
# into sys.path so we can import the mock implementations directly.
parent_dir = Path(__file__).resolve().parents[1]
mcp_server_dir = Path(__file__).resolve().parents[2] / "mcp-server"
sys.path.insert(0, str(parent_dir))
sys.path.insert(0, str(mcp_server_dir))

from adapters.mock import deployments  # noqa: E402
from adapters.mock import logs         # noqa: E402
from adapters.mock import metrics      # noqa: E402

# ── Instantiate mock adapters (module-level singletons) ────────────────
_metrics_adapter = metrics.MockMetrics()
_logs_adapter = logs.MockLogs()
_deployments_adapter = deployments.MockDeployments()

# ── LangChain / LangGraph imports ──────────────────────────────────────
from langchain.agents import create_agent           # noqa: E402
from langchain_core.tools import tool                # noqa: E402
from langchain_openai import ChatOpenAI              # noqa: E402
from langgraph.checkpoint.memory import MemorySaver    # noqa: E402

from agent import SYSTEM_PROMPT, TriageResult          # noqa: E402

# ── Tools that match TRIAGE_TOOLS ──────────────────────────────────────
# Names must be *exactly* what the agent expects so the LLM invokes them
# correctly (get_error_rate, query_logs, get_deployment_info, query_metrics).


@tool
def query_metrics(service: str) -> dict:
    """Query service metrics (CPU, memory, latency, throughput)."""
    return _metrics_adapter.get_metrics(service)


@tool
def get_error_rate(service: str) -> dict:
    """Return error rate, p95 latency and availability for a service."""
    return _metrics_adapter.get_error_rate(service)


@tool
def query_logs(service: str, level: str = "ERROR", limit: int = 20) -> list:
    """Query recent logs for a service, optionally filtered by level."""
    return _logs_adapter.query_logs(service, level, limit)


@tool
def get_deployment_info(service: str, deploy_id: str = "latest") -> dict:
    """Return recent deployment info for a service."""
    return _deployments_adapter.get_deployment_info(service, deploy_id)


# ── Compiled graph (module-level export for Studio) ────────────────────
triage_graph = create_agent(
    ChatOpenAI(
        model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
        temperature=0,
    ),
    tools=[
        query_metrics,
        get_error_rate,
        query_logs,
        get_deployment_info,
    ],
    system_prompt=SYSTEM_PROMPT,
    checkpointer=MemorySaver(),
    response_format=TriageResult,
)
