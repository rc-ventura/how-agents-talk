"""
TriageAgentExecutor — bridge between A2A protocol and the Triage Agent.

Uses the EventQueue API directly with TaskUpdater wrapper so
the protocol flow is explicit and visible

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
    UnsupportedOperationError,
    a2a_pb2,
)
from a2a.utils.errors import A2AError

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
            raise A2AError(error=InvalidParamsError())

        query = context.get_user_input()

        # ── 1. Create or recover the task ─────────────────────────────────
        task = context.current_task
        if not task:
            # Create task using protobuf directly (new_task was removed in 1.0.2)
            task = a2a_pb2.Task(
                id=context.task_id or context.message.task_id,
                context_id=context.context_id,
                status=a2a_pb2.TaskStatus(state=TaskState.TASK_STATE_SUBMITTED),
            )
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
                    message = updater.new_agent_message([Part(text=content)])
                    await updater.update_status(
                        TaskState.TASK_STATE_WORKING,
                        message,
                    )

                elif needs_input:
                    # ── 2b. Agent needs clarification from the user ────────
                    message = updater.new_agent_message([Part(text=content)])
                    await updater.update_status(
                        TaskState.TASK_STATE_INPUT_REQUIRED,
                        message,
                    )
                    break

                else:
                    # ── 2c. Task complete — publish artifact + final status ─
                    logger.info("Triage complete: %s", content[:120])

                    await updater.add_artifact(
                        [Part(text=content)],
                        name="triage-result",
                        last_chunk=True,
                    )

                    await updater.complete()
                    break

        except Exception as e:
            logger.exception("Triage Agent failed: %s", e)
            await updater.failed()
            raise A2AError(error=InternalError()) from e

    
    
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
        raise A2AError(error=UnsupportedOperationError())