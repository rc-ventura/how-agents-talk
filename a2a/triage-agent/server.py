"""
Triage Agent A2A Server.

Exposes the LangGraph Triage Agent via the A2A protocol at port 8002.

Run:
    OPENAI_API_KEY=... uv run python server.py

Endpoints:
    GET  /.well-known/agent.json  — AgentCard (agent discovery)
    POST /                        — A2A JSON-RPC (message/send, message/stream, tasks/get)

"""

import logging

import uvicorn
from a2a.server.apps import A2AStarletteApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore

from agent_card import AGENT_CARD
from agent_executor import TriageAgentExecutor

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

HOST = "0.0.0.0"
PORT = 8002


def build_app():
    request_handler = DefaultRequestHandler(
        agent_executor=TriageAgentExecutor(),
        task_store=InMemoryTaskStore(),
    )

    return A2AStarletteApplication(
        agent_card=AGENT_CARD,
        http_handler=request_handler,
    ).build()


if __name__ == "__main__":
    logger.info("Starting Triage Agent on http://%s:%d", HOST, PORT)
    logger.info("AgentCard at http://%s:%d/.well-known/agent.json", HOST, PORT)
    uvicorn.run(build_app(), host=HOST, port=PORT)