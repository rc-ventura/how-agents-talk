"""
TriageAgentExecutor — bridge between A2A protocol and the Triage Agent.

Uses the low-level EventQueue API directly (no TaskUpdater wrapper) so
the protocol flow is explicit and visible — educational by design.

The three A2A events used here:

  Task                    — published once when a new task is created
  TaskStatusUpdateEvent   — published to signal state changes:
                              submitted → working → completed | input_required | failed
  TaskArtifactUpdateEvent — published once with the final triage result

"""

import logging

from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import EventQueue
from a2a.server.tasks import TaskUpdater
from a2a.types import (
    InternalError,
    InvalidParamsError,
    Part,
    TaskState,
    TextPart,
    UnsupportedOperationError,
)
from a2a.utils import new_agent_text_message, new_task
from a2a.utils.errors import ServerError

from agent import TriageAgent

logger = logging.getLogger(__name__)


class TriageAgentExecutor(AgentExecutor):
    """Bridges A2A protocol to the LangChain Triage Agent.

    execute() is called for every incoming message/send or message/stream
    request. It drives the agent and publishes protocol events directly
    onto the EventQueue — no wrappers, no abstractions.
    """

    def __init__(self) -> None:
        self.agent = TriageAgent()


    async def execute(
        self,
        context: RequestContext,
        event_queue: EventQueue,
    ) -> None:
        if self._validate_request(context):
            raise ServerError(error=InvalidParamsError())

        query = context.get_user_input()

        # ── 1. Create or recover the task ─────────────────────────────────
        task = context.current_task
        if not task:
            task = new_task(context.message)
            # Publish the Task object so the server can persist it.
            await event_queue.enqueue_event(task)
        task_id = task.id
        context_id = task.context_id
        updater = TaskUpdater(event_queue, task_id, context_id)

        logger.info("Triage received query: %s", query[:80])

        try:
            # Match the official sample: update task state via TaskUpdater.
            # ── 2. Stream the agent ────────────────────────────────────────
            async for item in self.agent.stream(query, context_id):
                is_complete = item["is_task_complete"]
                needs_input = item["require_user_input"]
                content     = item["content"]

                if not is_complete and not needs_input:
                    # ── 2a. Intermediate update: agent is working ──────────
                    await updater.update_status(
                        TaskState.working,
                        new_agent_text_message(
                            content,
                            context_id,
                            task_id,
                        ),
                    )

                elif needs_input:
                    # ── 2b. Agent needs clarification from the user ────────
                    await updater.update_status(
                        TaskState.input_required,
                        new_agent_text_message(
                            content,
                            context_id,
                            task_id,
                        ),
                        final=True,
                    )
                    break

                else:
                    # ── 2c. Task complete — publish artifact + final status ─
                    logger.info("Triage complete: %s", content[:120])

                    await updater.add_artifact(
                        [Part(root=TextPart(text=content))],
                        name="triage-result",
                        last_chunk=True,
                    )

                    await updater.complete()
                    break

        except Exception as e:
            logger.exception("Triage Agent failed: %s", e)
            await updater.failed()
            raise ServerError(error=InternalError()) from e

    
    
    def _validate_request(self, context: RequestContext) -> bool:
        """Return True when the request is invalid."""
        if context is None:
            return True

        try:
            query = context.get_user_input()
        except Exception:
            return True

        if not query or not query.strip():
            return True

        if context.message is None:
            return True

        task = context.current_task
        if task is not None:
            if not task.id or not task.context_id:
                return True

        return False

    
    async def cancel(
        self,
        context: RequestContext,
        event_queue: EventQueue,
    ) -> None:
        raise ServerError(error=UnsupportedOperationError())