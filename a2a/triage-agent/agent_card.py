from google.protobuf import json_format
from a2a.types import AgentCard, AgentCapabilities, AgentInterface, AgentSkill


def build_agent_card() -> AgentCard:
    return AgentCard(
        name="Triage Agent",
        description=(
            "Classifies incidents by severity and category, identifies suspected cause, "
            "and recommends next steps."
        ),
        icon_url='http://localhost:8002/',
        version="1.0.0",
        default_input_modes=["text"],
        default_output_modes=["text"],
        capabilities=AgentCapabilities(streaming=True),
        supported_interfaces=[
            AgentInterface(
                url="http://localhost:8002",
                protocol_binding="JSONRPC",
            )
        ],
        skills=[
            AgentSkill(
                id="triage_incident",
                name="triage_incident",
                description=(
                    "Analyse a service alert using metrics, logs, and deployment data. "
                    "Produces a structured triage result with priority, category, "
                    "suspected cause, and recommended next step."
                ),
                tags=["incident", "triage", "classification", "priority"],
                examples=[
                    "Triage this alert: payments-service 34% error rate, deploy #4821",
                    "Classify and prioritise: payments-service is returning 500 errors since 02:51 UTC",
                ],
            )
        ],
    )

# Singleton instance
AGENT_CARD: AgentCard = build_agent_card()


def get_agent_card_json() -> str:
    """Serialise AgentCard to camelCase JSON (proto3 JSON mapping)."""
    return json_format.MessageToJson(AGENT_CARD)
