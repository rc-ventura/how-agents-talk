# Decisoes Tecnicas: Alinhamento com a2a-sdk v1.0.2

## Contexto

O projeto foi inicialmente construido contra a versao alpha `1.0.0a1` do `a2a-sdk`,
que quebrou varias APIs do codigo original. Posteriormente, o projeto foi
atualizado para a versao estavel `1.0.2`, que introduziu mudancas adicionais
na API. Abaixo estao as decisoes documentadas com base na inspecao do codigo-
fonte real da lib instalada em `.venv/lib/python3.13/site-packages/a2a/`.

---

## 1. server.py — Reescrita do bootstrap A2A

### Problema original

```python
from a2a.server.apps import A2AStarletteApplication  # ❌ nao existe
```

### Investigacao

Inspecionando `a2a/server/__init__.py` e o diretorio `a2a/server/`:

- `A2AStarletteApplication` foi **removido** da API publica.
- O servidor agora expoe funcoes puras em `a2a.server.routes`:
  - `create_agent_card_routes(agent_card)` → gera `GET /.well-known/agent-card.json`
  - `create_jsonrpc_routes(request_handler, rpc_url)` → gera `POST /`

### Decisao

Reescrever `build_app()` para montar manualmente uma aplicacao `Starlette`
usando essas funcoes de factory de rotas:

```python
from starlette.applications import Starlette
from a2a.server.routes import create_agent_card_routes, create_jsonrpc_routes

routes = []
routes.extend(create_jsonrpc_routes(request_handler, rpc_url="/"))
routes.extend(create_agent_card_routes(agent_card=AGENT_CARD))
return Starlette(routes=routes)
```

### Justificativa

Essa e a forma **oficial** recomendada pelo SDK atual. A abstracao
`A2AStarletteApplication` provavelmente foi removida para dar mais controle ao
usuario sobre middleware, CORS, lifespan events, etc.

### Correcao secundaria: endpoint well-known

A especificacao A2A exige `/.well-known/agent-card.json`. O codigo original
usava `agent.json` (sem `-card`). A constante
`a2a.utils.constants.AGENT_CARD_WELL_KNOWN_PATH` confirma o path correto:
`/.well-known/agent-card.json`.

---

## 2. agent_executor.py — Correcoes de API obsoleta

### Problema 1: `TextPart` removido

```python
from a2a.types import TextPart  # ❌ nao existe
# ...
Part(root=TextPart(text=content))  # ❌ TextPart nao existe
```

### Investigacao

Inspecionando `a2a/types/a2a_pb2.pyi`:

```python
class Part(_message.Message):
    __slots__ = ("text", "raw", "url", "data", "metadata", "filename", "media_type")
    text: str
    # ...
    def __init__(self, text: _Optional[str] = ..., ...)
```

`Part` e um message protobuf que aceita `text=` diretamente. Nao existe mais
`TextPart` como tipo separado.

### Decisao

Substituir por:

```python
Part(text=content)
```

---

### Problema 2: `ServerError` renomeado para `A2AError`

```python
from a2a.utils.errors import ServerError  # ❌ nao existe
```

### Investigacao

Inspecionando `a2a/utils/errors.py`:

```python
class A2AError(Exception): ...
# ServerError nao esta definido
```

### Decisao

Substituir todas as ocorrencias de `ServerError` por `A2AError`:

```python
from a2a.utils.errors import A2AError
# ...
raise A2AError(error=InvalidParamsError())
```

---

### Problema 3: `TaskState` enum renomeado

```python
TaskState.working           # ❌ AttributeError
TaskState.input_required    # ❌ AttributeError
```

### Investigacao

`TaskState` e um `EnumTypeWrapper` do protobuf (nao um enum Python comum).
Os nomes sao prefixados pelo nome do tipo:

```python
TaskState.TASK_STATE_WORKING
TaskState.TASK_STATE_INPUT_REQUIRED
TaskState.TASK_STATE_COMPLETED
TaskState.TASK_STATE_FAILED
```

### Decisao

Usar os nomes completos do protobuf:

```python
TaskState.TASK_STATE_WORKING
TaskState.TASK_STATE_INPUT_REQUIRED
```

---

### Problema 4: `DefaultRequestHandler` requer `agent_card`

```python
DefaultRequestHandler(
    agent_executor=...,
    task_store=...,
)  # ❌ TypeError: missing required argument 'agent_card'
```

### Investigacao

Inspecionando `a2a/server/request_handlers/default_request_handler.py:92`:

```python
def __init__(
    self,
    agent_executor: AgentExecutor,
    task_store: TaskStore,
    agent_card: AgentCard,  # <- obrigatorio
    ...
)
```

### Decisao

Passar o `AGENT_CARD` no construtor:

```python
DefaultRequestHandler(
    agent_executor=TriageAgentExecutor(),
    task_store=InMemoryTaskStore(),
    agent_card=AGENT_CARD,
)
```

---

## 3. mcp-server/server.py — FastMCP mudou de pacote

### Problema

```python
from mcp import FastMCP  # ❌ ImportError
```

### Investigacao

Inspecionando `mcp/__init__.py` e `mcp/server/__init__.py`:

- `FastMCP` foi movido de `mcp` para `mcp.server`
- O pacote `mcp` agora so expoe tipos e utilitarios de cliente

### Decisao

```python
from mcp.server import FastMCP
```

---

## 4. pyproject.toml — Dependencias faltantes

### Problema

O `pyproject.toml` original declarava apenas:

```toml
dependencies = ["a2a-sdk==1.0.0a1"]
```

Mas o codigo importava `langchain`, `langgraph`, `mcp`, `uvicorn`, etc.
O `uv` nao resolve transitivamente pacotes que nao estao declarados, entao
essas importacoes quebravam.

### Decisao

Adicionar todas as dependencias diretas explicitamente, com version ranges
baseados no que o `uv sync` realmente resolveu:

```toml
dependencies = [
    "a2a-sdk==1.0.0a1",
    "langchain>=1.2.0",
    "langchain-core>=1.3.0",
    "langchain-openai>=1.2.0",
    "langchain-mcp-adapters>=0.2.0",
    "langgraph>=1.1.0",
    "mcp>=1.27.0",
    "uvicorn>=0.46.0",
    "pydantic>=2.0.0",
]
```

### Nota sobre versoes

Os pins iniciais que eu sugeri (`>=0.3.0` para langchain) estavam
**desatualizados**. O `uv` resolveu para versoes muito mais recentes:
- `langchain`: 0.3.x → **1.2.15**
- `langgraph`: 0.2.x → **1.1.9**
- `mcp`: 1.0.x → **1.27.0**

Isso demonstra que ranges permissivos sao melhores para projetos alpha — o
resolver do `uv` pega o mais recente compativel.

---

## 5. agent_card.py — Alinhamento com protobuf da lib

### Decisoes baseadas em `a2a/types/a2a_pb2.pyi`

| Campo | Status | Justificativa |
|---|---|---|
| `protocol_version` em `AgentInterface` | **Adicionado** | Campo existe no protobuf; tutorial oficial usa `"1.0"` |
| `provider` em `AgentCard` | **Adicionado** | Campo existe no protobuf; ausencia gera default vazio |
| `push_notifications` em `AgentCapabilities` | **Adicionado** | Campo booleano obrigatorio no protobuf; default `False` |
| `input_modes`/`output_modes` em `AgentSkill` | **Adicionados** | Campos existentes no protobuf; melhoram descoberta |

Todos sao opcionais no protobuf (proto3), mas a **spec oficial** os recomenda
para descoberta correta de agentes.

---

## Metodologia

Todas as decisoes foram tomadas por **inspecao direta do codigo-fonte da lib**
instalada, nao por documentacao externa:

```bash
# Verificar se um modulo existe
uv run python -c "import a2a.server.apps"  # ImportError

# Listar membros de um modulo
uv run python -c "import a2a.server.routes; print(dir(a2a.server.routes))"

# Inspecionar assinatura de classe
python -c "from a2a.server.request_handlers import DefaultRequestHandler;
import inspect; print(inspect.signature(DefaultRequestHandler.__init__))"

# Ler protobuf definitions
cat .venv/lib/python3.13/site-packages/a2a/types/a2a_pb2.pyi
```

Essa abordagem e necessaria porque:
1. O `a2a-sdk` esta em alpha e a documentacao online pode estar desatualizada
2. O tutorial oficial (a2a-protocol.org) pode refletir uma versao diferente
3. O codigo-fonte da lib e a unica fonte de verdade para uma lib em desenvolvimento

---

## Resultado

Apos todas as correcoes:

```bash
uv run python -c "
from agent import TriageAgent
from agent_executor import TriageAgentExecutor
from server import build_app
from mcp.server import FastMCP
print('Todas as importacoes funcionam')
"
```

Sucesso. Todas as incompatibilidades entre o codigo original e o
`a2a-sdk==1.0.0a1` foram resolvidas.

---

## 6. agent_executor.py — Migracao para a2a-sdk v1.0.2

### Problema: Funcoes utilitarias removidas de `a2a.utils`

```python
from a2a.utils import new_agent_text_message, new_task  # ❌ removido em 1.0.2
```

### Investigacao

Inspecionando `a2a/utils/__init__.py` na versao 1.0.2:

```python
# a2a.utils agora exporta apenas:
- AGENT_CARD_WELL_KNOWN_PATH
- DEFAULT_RPC_URL
- TransportProtocol
- constants
- errors
- proto_utils
- to_stream_response
```

As funcoes `new_agent_text_message` e `new_task` foram **removidas** da API publica.
A nova abordagem e usar metodos da classe `TaskUpdater` para criar mensagens e
gerenciar tarefas.

### Decisao 1: Substituir `new_agent_text_message` por `TaskUpdater.new_agent_message`

**Antes (1.0.0a1):**

```python
from a2a.utils import new_agent_text_message
# ...
await updater.update_status(
    TaskState.TASK_STATE_WORKING,
    new_agent_text_message(content, context_id, task_id),
)
```

**Depois (1.0.2):**

```python
from a2a.types import Part
# ...
message = updater.new_agent_message([Part(text=content)])
await updater.update_status(
    TaskState.TASK_STATE_WORKING,
    message,
)
```

**Justificativa:**

Inspecionando `a2a/server/tasks/task_updater.py`:

```python
class TaskUpdater:
    def new_agent_message(self, parts: list[a2a_pb2.Part], metadata: dict[str, Any] | None = None) -> a2a_pb2.Message:
        """Cria uma mensagem do agente com as partes fornecidas."""
```

O metodo `TaskUpdater.new_agent_message()` e a forma oficial de criar mensagens
do agente em 1.0.2. Ele recebe uma lista de `Part` (protobuf) e retorna um
objeto `Message` pronto para uso.

### Decisao 2: Substituir `new_task` por criacao direta via protobuf

**Antes (1.0.0a1):**

```python
from a2a.utils import new_task
# ...
task = new_task(context.message)
await event_queue.enqueue_event(task)
```

**Depois (1.0.2):**

```python
from a2a.types import a2a_pb2, TaskState
# ...
task = a2a_pb2.Task(
    id=context.task_id or context.message.task_id,
    context_id=context.context_id,
    status=a2a_pb2.TaskStatus(state=TaskState.TASK_STATE_SUBMITTED),
)
await event_queue.enqueue_event(task)
```

**Justificativa:**

Inspecionando `a2a/types/a2a_pb2.pyi`:

```python
class Task(_message.Message):
    id: str
    context_id: str
    status: TaskStatus
    # ...
```

A funcao `new_task` foi removida. A nova abordagem e criar o objeto `Task`
diretamente via protobuf. O campo `status` requer um objeto `TaskStatus` (nao
um enum direto), que deve ser instanciado com o estado desejado.

### Decisao 3: Adicionar import de `a2a_pb2`

```python
from a2a.types import (
    InternalError,
    InvalidParamsError,
    Part,
    TaskState,
    UnsupportedOperationError,
    a2a_pb2,  # ← adicionado para acesso direto aos tipos protobuf
)
```

**Justificativa:**

A criacao direta de objetos protobuf requer acesso aos tipos definidos em
`a2a.types.a2a_pb2`. Isso e necessario para:
- Criar objetos `Task` com `a2a_pb2.Task(...)`
- Criar objetos `TaskStatus` com `a2a_pb2.TaskStatus(...)`
- Acessar outros tipos protobuf conforme necessario

### Verificacao de compatibilidade

As seguintes APIs permaneceram inalteradas entre 1.0.0a1 e 1.0.2:
- `TaskState.TASK_STATE_WORKING` e outros estados (enum protobuf)
- `Part(text=...)` (construtor de Part)
- `A2AError` (excecao de erro)
- `DefaultRequestHandler` (assinatura compativel, parametros adicionais sao opcionais)
- `create_agent_card_routes` e `create_jsonrpc_routes` (factory functions)
- `TaskUpdater` (classe principal, metodos de conveniencia adicionados)

### Resultado

Apos a migracao para 1.0.2:

```bash
cd a2a/triage-agent
uv run python -c "
from agent_executor import TriageAgentExecutor
from server import build_app
from agent import TriageAgent
print('Todas as importacoes funcionam com 1.0.2')
"
```

Sucesso. O codigo foi migrado para `a2a-sdk==1.0.2` com sucesso.
