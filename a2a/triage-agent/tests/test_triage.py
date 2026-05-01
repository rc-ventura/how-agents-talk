"""CLI smoke-test for the Triage Agent (Studio graph).

Runs a single invocation against the compiled graph with mock tools and
prints the structured TriageResult.  No MCP server or Studio required.

Usage:
    cd a2a/triage-agent
    uv run python tests/smoke_test.py "Triage this alert: payments-service 34% error rate, deploy #4821"
"""

from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path
from typing import Any

# Make studio/ importable when running from tests/
parent_dir = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(parent_dir))

from studio.triage_graph import triage_graph


def _print_result(result: dict[str, Any]) -> None:
    """Pretty-print the agent output (structured or raw)."""
    print("\n" + "=" * 60)
    print("RESULT")
    print("=" * 60)

    # The graph returns a dict; structured output is in 'structured_response'
    structured = result.get("structured_response")
    if structured is None:
        # Fallback: print whatever keys we got
        for key, value in result.items():
            print(f"\n{key}:")
            print(value)
        return

    print(f"\nPriority : {structured.priority}")
    print(f"Category : {structured.category}")
    print(f"Suspected Cause : {structured.suspected_cause}")
    print(f"Recommended Next: {structured.recommended_next_step}")
    print(f"Confidence : {structured.confidence}")
    print("=" * 60)


async def run_triage(message: str) -> None:
    config = {"configurable": {"thread_id": "cli-test-001"}}

    # Invoke the compiled graph 
    result = await triage_graph.ainvoke(
        {"messages": [{"role": "user", "content": message}]},
        config=config,
    )
    _print_result(result)


def main() -> None:
    parser = argparse.ArgumentParser(description="Smoke-test the Triage Agent")
    parser.add_argument(
        "message",
        nargs="?",
        default="Triage this alert: payments-service 34% error rate, deploy #4821",
        help="User message to send to the agent",
    )
    args = parser.parse_args()

    asyncio.run(run_triage(args.message))


if __name__ == "__main__":
    main()
