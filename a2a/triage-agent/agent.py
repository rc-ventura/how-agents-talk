"""
Triage Agent — LangChain v1 + MCP tools.

This agent is responsible for triaging incidents and producing a structured triage result.

It uses the following tools:
- get_error_rate
- query_logs
- get_deployment_info
- query_metrics

It produces a structured triage result with the following fields:
- status: "completed" | "input_required" | "error"
- priority: "low" | "medium" | "high" | "critical"
- category: e.g. "deployment_regression", "database_error", "memory_leak"
- suspected_cause: one clear sentence describing the likely root cause
- recommended_next_step: what the Investigation Agent should focus on
- confidence: 0.0-1.0

"""

import json
import os
import asyncio

from collections.abc import AsyncIterable
from typing import Any, ClassVar, Literal 

from langchain.agents import create_agent
from langchain_core.messages import AIMessage, ToolMessage
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import MemorySaver
from pydantic import BaseModel

MCP_SERVER_URL = os.getenv("MCP_SERVER_URL", "http://localhost:8001/mcp")

SYSTEM_PROMPT = """You are the Triage Agent for an incident response system.

Your job is to analyse a service alert and produce a structured triage result.

When you receive an alert:
1. Use get_error_rate to confirm the current error rate.
2. Use query_logs to find the dominant error pattern.
3. Use get_deployment_info to check if a recent deployment coincides with the incident.
4. Based on your findings, fill in each field of the structured response:
   - priority: "low" | "medium" | "high" | "critical"
   - category: e.g. "deployment_regression", "database_error", "memory_leak"
   - suspected_cause: one clear sentence describing the likely root cause
   - recommended_next_step: what the Investigation Agent should focus on
   - confidence: 0.0-1.0
"""

class TriageResult(BaseModel):
    """Structured triage output enforced by the graph via Pydantic."""

    status: Literal["completed", "input_required", "error"] = "input_required"
    priority: Literal["low", "medium", "high", "critical"] = "low"
    category: str = ""
    suspected_cause: str = ""
    recommended_next_step: str = ""
    confidence: float = 0.0

# Only the tools this agent needs 
TRIAGE_TOOLS = {"get_error_rate", "query_logs", "get_deployment_info", "query_metrics"}


class TriageAgent:
    """LangChain v1 agent wrapped around MCP tools.

    The compiled graph is built once (lazy) and reused across calls.
    ProviderStrategy (auto-selected for OpenAI) enforces the TriageResult
    schema via native structured output — no prompt-only JSON.
    MemorySaver keeps message history per context_id (thread).

    Exposes a stream() async generator so the executor can yield
    intermediate A2A status events while the agent is working.

    The MCP client and tools are cached as class variables so every
    instance (and the whole process) reuses a single connection.
    """

    _mcp_client: ClassVar[MultiServerMCPClient | None] = None
    _tools_cache: ClassVar[list | None] = None

    def __init__(self) -> None:
        self.model = ChatOpenAI(
            model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            temperature=0,
        )
        self._memory = MemorySaver()
        self._agent = None
        self._lock = asyncio.Lock()

    async def _get_agent(self):
        """Lazy-init: fetch MCP tools and compile the graph once (thread-safe).

        The MultiServerMCPClient and the tool list are cached at class
        level so all instances share the same connection.
        """
        if self._agent is not None:
            return self._agent

        async with self._lock:
            if self._agent is not None:
                return self._agent

            if TriageAgent._mcp_client is None:
                TriageAgent._mcp_client = MultiServerMCPClient(
                    {
                        "incident-response": {
                            "transport": "streamable-http",
                            "url": MCP_SERVER_URL,
                        }
                    }
                )
                all_tools = await TriageAgent._mcp_client.get_tools()
                TriageAgent._tools_cache = [
                    t for t in all_tools if t.name in TRIAGE_TOOLS
                ]

            self._agent = create_agent(
                self.model,
                tools=TriageAgent._tools_cache,
                system_prompt=SYSTEM_PROMPT,
                checkpointer=self._memory,
                response_format=TriageResult,
            )
        return self._agent

    async def stream(
        self, query: str, context_id: str
    ) -> AsyncIterable[dict[str, Any]]:
        """Invoke the agent and yield intermediate + final results.

        Each yielded dict has:
          is_task_complete   — True only on the final item
          require_user_input — True if agent needs clarification
          content            — text payload for this event
        """
        agent = await self._get_agent()
        inputs = {"messages": [{"role": "user", "content": query}]}
        config = {"configurable": {"thread_id": context_id}}

        # stream_mode='values' yields the full state after each step.
        # chunk["messages"][-1] is always the latest message.
        async for chunk in agent.astream(inputs, config, stream_mode="values"):
            last = chunk["messages"][-1]

            if isinstance(last, AIMessage) and last.tool_calls:
                tool_name = last.tool_calls[0].get("name", "tool")
                yield {
                    "is_task_complete": False,
                    "require_user_input": False,
                    "content": f"Calling tool: {tool_name}...",
                }

            elif isinstance(last, ToolMessage):
                yield {
                    "is_task_complete": False,
                    "require_user_input": False,
                    "content": "Processing tool result...",
                }

        yield self._get_agent_response(agent, config)

    def _get_agent_response(self, agent, config: dict) -> dict[str, Any]:
        """Read structured_response from graph state after streaming completes."""
        state = agent.get_state(config)
        structured: TriageResult | None = state.values.get("structured_response")

        if structured and isinstance(structured, TriageResult):
            if structured.status == "completed":
                content = json.dumps(
                    {
                        "priority": structured.priority,
                        "category": structured.category,
                        "suspected_cause": structured.suspected_cause,
                        "recommended_next_step": structured.recommended_next_step,
                        "confidence": structured.confidence,
                    },
                    indent=2,
                )
                return {
                    "is_task_complete": True,
                    "require_user_input": False,
                    "content": content,
                }
            elif structured.status == "input_required":
                return {
                    "is_task_complete": False,
                    "require_user_input": True,
                    "content": structured.suspected_cause or "More information needed.",
                }

        return {
            "is_task_complete": False,
            "require_user_input": True,
            "content": "Unable to complete triage. Please try again.",
        }
