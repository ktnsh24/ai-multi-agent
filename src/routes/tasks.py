"""Task management routes."""

import asyncio
import logging

from fastapi import APIRouter, BackgroundTasks, HTTPException, Request

from src.models import (
    AgentEvent,
    EventType,
    TaskRequest,
    TaskResponse,
    TaskResult,
    TaskStatus,
    TaskSummary,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/v1/tasks", tags=["tasks"])


@router.post("", response_model=TaskResponse)
async def submit_task(
    request: TaskRequest,
    app_request: Request,
    background_tasks: BackgroundTasks,
) -> TaskResponse:
    """Submit a new task for the crew to work on."""
    task_store = app_request.app.state.task_store
    crew = app_request.app.state.crew_orchestrator
    ws_manager = app_request.app.state.ws_manager

    # Create task record
    task_response = await task_store.create_task(request)

    # Run crew in background
    background_tasks.add_task(
        _run_crew_task,
        crew=crew,
        request=request,
        task_id=task_response.task_id,
        task_store=task_store,
        ws_manager=ws_manager,
    )

    return task_response


@router.get("", response_model=list[TaskSummary])
async def list_tasks(app_request: Request, limit: int = 20) -> list[TaskSummary]:
    """List all tasks."""
    task_store = app_request.app.state.task_store
    return await task_store.list_tasks(limit=limit)


@router.get("/{task_id}", response_model=TaskResult)
async def get_task(task_id: str, app_request: Request) -> TaskResult:
    """Get task details and result."""
    task_store = app_request.app.state.task_store
    task = await task_store.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@router.delete("/{task_id}")
async def delete_task(task_id: str, app_request: Request) -> dict:
    """Delete a task."""
    task_store = app_request.app.state.task_store
    deleted = await task_store.delete_task(task_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Task not found")
    return {"deleted": True}


async def _run_crew_task(
    crew,
    request: TaskRequest,
    task_id: str,
    task_store,
    ws_manager,
) -> None:
    """Background task: run the crew and broadcast events."""
    try:
        # Update status to running
        await task_store.update_task(task_id, TaskStatus.RUNNING)

        # Event callback that broadcasts to WebSocket
        async def event_callback(event: AgentEvent) -> None:
            event.task_id = task_id
            await ws_manager.broadcast(event)

        # Run crew
        result = await crew.run(request, event_callback=event_callback)

        # Update with results
        await task_store.update_task(
            task_id,
            TaskStatus.COMPLETED,
            result=result["result"],
            agent_outputs=result["agent_outputs"],
            iterations=result["iterations"],
            latency_ms=result["latency_ms"],
        )

        # Broadcast completion
        await ws_manager.broadcast(
            AgentEvent(
                type=EventType.TASK_COMPLETED,
                task_id=task_id,
                content=result["result"][:500],
            )
        )

    except Exception as e:
        logger.error("Crew task failed: %s", str(e), exc_info=True)
        await task_store.update_task(task_id, TaskStatus.FAILED)
        await ws_manager.broadcast(
            AgentEvent(
                type=EventType.TASK_FAILED,
                task_id=task_id,
                content=str(e),
            )
        )
