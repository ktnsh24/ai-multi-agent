"""Task persistence — store task submissions and results."""

from abc import ABC, abstractmethod
from datetime import datetime
from uuid import uuid4

from src.models import (
    TaskRequest,
    TaskResponse,
    TaskResult,
    TaskStatus,
    TaskSummary,
)


class BaseTaskStore(ABC):
    """Abstract base class for task storage."""

    @abstractmethod
    async def create_task(self, request: TaskRequest) -> TaskResponse: ...

    @abstractmethod
    async def get_task(self, task_id: str) -> TaskResult | None: ...

    @abstractmethod
    async def list_tasks(self, limit: int = 20) -> list[TaskSummary]: ...

    @abstractmethod
    async def update_task(
        self,
        task_id: str,
        status: TaskStatus,
        result: str | None = None,
        agent_outputs: dict[str, str] | None = None,
        iterations: int = 0,
        latency_ms: float = 0.0,
    ) -> None: ...

    @abstractmethod
    async def delete_task(self, task_id: str) -> bool: ...


class InMemoryTaskStore(BaseTaskStore):
    """In-memory task store for development and testing."""

    def __init__(self) -> None:
        self.tasks: dict[str, dict] = {}

    async def create_task(self, request: TaskRequest) -> TaskResponse:
        task_id = str(uuid4())
        now = datetime.utcnow()

        self.tasks[task_id] = {
            "task_id": task_id,
            "topic": request.topic,
            "crew_mode": request.crew_mode,
            "agents": request.agents,
            "status": TaskStatus.PENDING,
            "result": None,
            "agent_outputs": {},
            "iterations": 0,
            "latency_ms": 0.0,
            "context": request.context,
            "created_at": now,
            "completed_at": None,
        }

        return TaskResponse(
            task_id=task_id,
            status=TaskStatus.PENDING,
            topic=request.topic,
            crew_mode=request.crew_mode,
            agents=request.agents,
            created_at=now,
        )

    async def get_task(self, task_id: str) -> TaskResult | None:
        task = self.tasks.get(task_id)
        if not task:
            return None

        return TaskResult(
            task_id=task["task_id"],
            status=task["status"],
            topic=task["topic"],
            crew_mode=task["crew_mode"],
            result=task["result"] or "",
            agent_outputs=task["agent_outputs"],
            iterations=task["iterations"],
            latency_ms=task["latency_ms"],
            created_at=task["created_at"],
            completed_at=task["completed_at"],
        )

    async def list_tasks(self, limit: int = 20) -> list[TaskSummary]:
        sorted_tasks = sorted(self.tasks.values(), key=lambda t: t["created_at"], reverse=True)
        return [
            TaskSummary(
                task_id=t["task_id"],
                topic=t["topic"],
                status=t["status"],
                crew_mode=t["crew_mode"],
                agents=t["agents"],
                created_at=t["created_at"],
                completed_at=t["completed_at"],
            )
            for t in sorted_tasks[:limit]
        ]

    async def update_task(
        self,
        task_id: str,
        status: TaskStatus,
        result: str | None = None,
        agent_outputs: dict[str, str] | None = None,
        iterations: int = 0,
        latency_ms: float = 0.0,
    ) -> None:
        if task_id not in self.tasks:
            return

        self.tasks[task_id]["status"] = status
        if result is not None:
            self.tasks[task_id]["result"] = result
        if agent_outputs:
            self.tasks[task_id]["agent_outputs"] = agent_outputs
        self.tasks[task_id]["iterations"] = iterations
        self.tasks[task_id]["latency_ms"] = latency_ms

        if status in (TaskStatus.COMPLETED, TaskStatus.FAILED):
            self.tasks[task_id]["completed_at"] = datetime.utcnow()

    async def delete_task(self, task_id: str) -> bool:
        if task_id in self.tasks:
            del self.tasks[task_id]
            return True
        return False


def create_task_store() -> BaseTaskStore:
    """Factory function to create the appropriate task store."""
    return InMemoryTaskStore()
