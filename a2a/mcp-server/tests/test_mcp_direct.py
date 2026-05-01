"""Teste direto: TriageAgent conectando ao MCP via MultiServerMCPClient.

Não usa protocolo A2A - chama o agente diretamente para testar a conexão MCP.

Usage:
    cd /Users/rafaelventura/Desktop/how-agents-talk
    uv run python test_mcp_direct.py
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "triage-agent"))

async def main():
    from agent import TriageAgent

    print("Criando TriageAgent...")
    agent = TriageAgent()

    print("Testando conexão MCP e triage...")
    message = "Triage this alert: payments-service 34% error rate, deploy #4821"
    
    try:
        async for event in agent.stream("payments-service", message):
            event_type = event.get("event", "unknown")
            content = event.get("content", "")
            print(f"[{event_type}]")
            if isinstance(content, dict):
                import json
                print(json.dumps(content, indent=2))
            elif content:
                print(content)
    except Exception as e:
        print(f"ERRO: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
