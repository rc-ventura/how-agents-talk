# how-agents-talk

> A practical demonstration of **Agent-to-Agent (A2A)** and **Model Context Protocol (MCP)** working together to resolve a production incident — implemented across four different AI frameworks.

![Architecture](assets/1776208611270.png)

---

## What this is

A **payments-service** fires a 34% error rate alert. An orchestrator receives it and delegates to four specialist agents — each built with a different framework — all communicating via A2A and sharing tools via MCP.

| Variant | Approach | LLM | Status |
|---|---|---|---|
| `a2a/` | Cross-framework via A2A SDK | OpenAI / Anthropic / Gemini | 🚧 In progress |
| `beeai/` | BeeAI + Ollama | Local (Granite, Llama, etc.) | 📋 Planned |

---

## Architecture

```
Incident alert: payments-service 34% error rate
        │
        ▼
┌─────────────────────────────────┐
│  Orchestrator  (LangGraph)      │  ← receives alert, delegates via A2A
└──────┬──────┬──────┬────────────┘
       │ A2A  │ A2A  │ A2A   │ A2A
       ▼      ▼      ▼       ▼
  Triage  Invest.  Remedi.  Comms
 LangGraph  ADK   OpenAI   CrewAI
       │      │      │       │
       └──────┴──────┴───────┘
                  │
                  ▼
       ┌──────────────────────┐
       │      MCP Server      │  ← FastMCP · shared tools for all agents
       │  (FastMCP + ports    │
       │   & adapters)        │
       └──────────────────────┘
    query_metrics · query_logs
    get_deployment_info · execute_rollback · notify
```

**A2A** is the communication bus between agents — each agent exposes an `agent_card.json` describing its capabilities, and agents discover each other dynamically.

**MCP** is the shared tooling layer — any MCP-compatible agent calls `query_metrics`, `query_logs`, etc. without knowing the underlying data source.

---

## Project Structure

```
how-agents-talk/
│
├── a2a/                            # cross-framework via A2A SDK
│   ├── mcp-server/                 # FastMCP — shared tools backend
│   │   ├── server.py
│   │   ├── deps.py                 # composition root — swaps adapters via env vars
│   │   ├── ports/                  # Python Protocol contracts
│   │   │   ├── metrics.py
│   │   │   ├── logs.py
│   │   │   ├── deployments.py
│   │   │   └── notifications.py
│   │   └── adapters/
│   │       └── mock/               # default — no credentials needed
│   │           ├── metrics.py
│   │           ├── logs.py
│   │           ├── deployments.py
│   │           └── notifications.py
│   └── problem/                    # shared scenario: contracts + mock data
│       ├── contracts/
│       │   └── models.py           # Pydantic models (Alert, TriageResult, …)
│       └── mocks/
│           └── data.py             # in-memory mock state
│
└── beeai/                          # 📋 planned — BeeAI + Ollama local
```

---

## Quickstart

### Run with mocks (no credentials)

```bash
# Start the MCP server
cd a2a/mcp-server
fastmcp run server.py --transport http --port 8000
```

### Run with real integrations

```bash
METRICS_ADAPTER=datadog \
LOGS_ADAPTER=datadog \
NOTIFICATIONS_ADAPTER=pagerduty \
DD_API_KEY=... DD_APP_KEY=... \
PD_API_KEY=... PD_SERVICE_ID=... \
fastmcp run a2a/mcp-server/server.py --transport http --port 8000
```

---

## MCP Tools

| Tool | Description |
|---|---|
| `query_metrics` | Current operational metrics for a service |
| `get_error_rate` | Error rate + health status (healthy / degraded / critical) |
| `query_logs` | Recent log entries filtered by level (ERROR / WARN / INFO / ALL) |
| `get_deployment_info` | Deployment details including applied migrations |
| `execute_rollback` | Roll back a deployment to the previous stable version |
| `notify_team` | Send incident notification (`team` channel or `escalation` for critical) |
| `create_incident_report` | Structured post-incident report |

---

## Ports & Adapters

The MCP server uses the [hexagonal architecture](https://alistair.cockburn.us/hexagonal-architecture/) pattern. Ports are Python `Protocol` contracts; adapters are swapped at startup via env vars — `server.py` never changes.

```
METRICS_ADAPTER=mock      → a2a/mcp-server/adapters/mock/metrics.py       (default)
METRICS_ADAPTER=datadog   → a2a/mcp-server/adapters/datadog/metrics.py    (needs DD_API_KEY)

NOTIFICATIONS_ADAPTER=mock      → a2a/mcp-server/adapters/mock/notifications.py
NOTIFICATIONS_ADAPTER=pagerduty → a2a/mcp-server/adapters/pagerduty/notifications.py
```

---

## Frameworks Used

| Agent | Framework | Why | Status |
|---|---|---|---|
| Orchestrator | LangGraph | Graph-based flow + Studio UI for visualization | 📋 Planned |
| Triage | LangGraph | State machine for severity classification | 📋 Planned |
| Investigation | Google ADK | Tool-use + structured reasoning | 📋 Planned |
| Remediation | OpenAI SDK | Direct tool calls, minimal abstraction | 📋 Planned |
| Communication | CrewAI | Role-based crew for report generation | 📋 Planned |
| BeeAI variant | BeeAI + Ollama | Local inference, no API costs | 📋 Planned |

---

## References

- [A2A Protocol](https://google.github.io/A2A/)
- [Model Context Protocol](https://modelcontextprotocol.io/)
- [FastMCP](https://github.com/jlowin/fastmcp)
- [Architecting Agentic MLOps — A2A + MCP](https://www.infoq.com/) — InfoQ, Feb 2026