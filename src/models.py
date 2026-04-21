"""Pydantic models for the multi-agent platform."""

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


# ─── Enums ─────────────────────────────────────────────────────

class TaskStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class AgentRole(str, Enum):
    RESEARCHER = "researcher"
    ANALYST = "analyst"
    WRITER = "writer"
    CRITIC = "critic"


class CrewMode(str, Enum):
    SEQUENTIAL = "sequential"
    HIERARCHICAL = "hierarchical"


class EventType(str, Enum):
    TASK_STARTED = "task_started"
    AGENT_THINKING = "agent_thinking"
    AGENT_ACTION = "agent_action"
    AGENT_RESULT = "agent_result"
    AGENT_DELEGATION = "agent_delegation"
    CREW_PROGRESS = "crew_progress"
    TASK_COMPLETED = "task_completed"
    TASK_FAILED = "task_failed"
    ERROR = "error"


# ─── Request Models ────────────────────────────────────────────

class TaskRequest(BaseModel):
    """Request to submit a new task for the crew."""

    topic: str = Field(description="The topic or question for the crew to work on")
    crew_mode: CrewMode = Field(default=CrewMode.SEQUENTIAL, description="Crew orchestration mode")
    agents: list[AgentRole] = Field(
        default=[AgentRole.RESEARCHER, AgentRole.ANALYST, AgentRole.WRITER, AgentRole.CRITIC],
        description="Which agents to include in the crew",
    )
    max_iterations: int = Field(default=15, ge=1, le=50, description="Max iterations per agent")
    context: str | None = Field(default=None, description="Additional context for the task")


# ─── Response Models ───────────────────────────────────────────

class TaskResponse(BaseModel):
    """Response after submitting a task."""

    task_id: str
    status: TaskStatus
    topic: str
    crew_mode: CrewMode
    agents: list[AgentRole]
    created_at: datetime


class TaskResult(BaseModel):
    """Final result of a completed task."""

    task_id: str
    status: TaskStatus
    topic: str
    crew_mode: CrewMode
    result: str
    agent_outputs: dict[str, str] = Field(default_factory=dict)
    iterations: int = 0
    latency_ms: float = 0.0
    created_at: datetime
    completed_at: datetime | None = None


class TaskSummary(BaseModel):
    """Summary of a task for listing."""

    task_id: str
    topic: str
    status: TaskStatus
    crew_mode: CrewMode
    agents: list[AgentRole]
    created_at: datetime
    completed_at: datetime | None = None


# ─── WebSocket Events ──────────────────────────────────────────

class AgentEvent(BaseModel):
    """Real-time event from agent execution."""

    type: EventType
    task_id: str
    agent: AgentRole | None = None
    content: str = ""
    metadata: dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.utcnow)


# ─── Health Model ──────────────────────────────────────────────

class HealthStatus(BaseModel):
    status: str = "healthy"
    version: str = "0.1.0"
    provider: str = ""
    components: dict[str, str] = Field(default_factory=dict)
