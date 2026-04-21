# Pydantic Models Reference — ai-multi-agent

> Complete reference for all Pydantic models, enums, and settings used in the multi-agent system

---

## Table of Contents

1. [Enums](#enums)
2. [Request Models](#request-models)
3. [Response Models](#response-models)
4. [Event Models](#event-models)
5. [Settings](#settings)
6. [Serialization Examples](#serialization-examples)

---

## Enums

### `CloudProvider`

```python
class CloudProvider(str, Enum):
    LOCAL = "local"
    AWS = "aws"
    AZURE = "azure"
```

Determines which LLM provider and task store implementation to use.

| Value | LLM Provider | Task Store |
|-------|-------------|------------|
| `local` | `OllamaProvider` | `InMemoryTaskStore` |
| `aws` | `BedrockProvider` | `PostgresTaskStore` |
| `azure` | `AzureOpenAIProvider` | `PostgresTaskStore` |

### `AppEnvironment`

```python
class AppEnvironment(str, Enum):
    LOCAL = "local"
    DEV = "dev"
    STAGING = "staging"
    PROD = "prod"
```

Controls logging level, debug mode, and CORS settings.

### `AgentRole`

```python
class AgentRole(str, Enum):
    RESEARCHER = "researcher"
    ANALYST = "analyst"
    WRITER = "writer"
    CRITIC = "critic"
```

Identifies which agent produced an event. Used in `AgentEvent` for WebSocket event routing and frontend color-coding.

### `CrewMode`

```python
class CrewMode(str, Enum):
    SEQUENTIAL = "sequential"
    HIERARCHICAL = "hierarchical"
```

| Mode | Execution | Use Case |
|------|-----------|----------|
| `sequential` | Fixed order: R→A→W→C | Predictable pipelines |
| `hierarchical` | Manager delegates dynamically | Complex, iterative tasks |

### `TaskStatus`

```python
class TaskStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
```

State machine:

```
PENDING → RUNNING → COMPLETED
                  → FAILED
```

### `EventType`

```python
class EventType(str, Enum):
    TASK_STARTED = "task_started"
    AGENT_THINKING = "agent_thinking"
    AGENT_ACTION = "agent_action"
    AGENT_RESULT = "agent_result"
    TASK_COMPLETED = "task_completed"
    ERROR = "error"
```

| Event | When | Data Contains |
|-------|------|---------------|
| `task_started` | Crew begins execution | `task_id` |
| `agent_thinking` | Agent reasoning step | `thought` string |
| `agent_action` | Agent uses a tool | `action` name, `input` |
| `agent_result` | Agent produces output | `result` content |
| `task_completed` | All agents finished | `result` final output |
| `error` | Failure during execution | `error` message |

---

## Request Models

### `TaskRequest`

```python
class TaskRequest(BaseModel):
    """Request body for POST /v1/tasks."""

    topic: str = Field(
        ...,
        min_length=1,
        max_length=500,
        description="The topic for the agent crew to research and report on",
    )
    crew_mode: CrewMode = Field(
        default=CrewMode.SEQUENTIAL,
        description="Orchestration mode: sequential or hierarchical",
    )
```

**Example JSON:**

```json
{
    "topic": "Impact of AI on healthcare",
    "crew_mode": "sequential"
}
```

**Validation rules:**
- `topic`: Required, 1-500 characters
- `crew_mode`: Optional, defaults to `sequential`

---

## Response Models

### `TaskResult`

```python
class TaskResult(BaseModel):
    """Stored task with status and result."""

    task_id: str
    topic: str
    crew_mode: CrewMode
    status: TaskStatus = TaskStatus.PENDING
    result: str | None = None
    error: str | None = None
    created_at: datetime
    completed_at: datetime | None = None

    model_config = ConfigDict(use_enum_values=True)
```

**Example JSON (pending):**

```json
{
    "task_id": "550e8400-e29b-41d4-a716-446655440000",
    "topic": "Impact of AI on healthcare",
    "crew_mode": "sequential",
    "status": "pending",
    "result": null,
    "error": null,
    "created_at": "2025-01-15T10:30:00Z",
    "completed_at": null
}
```

**Example JSON (completed):**

```json
{
    "task_id": "550e8400-e29b-41d4-a716-446655440000",
    "topic": "Impact of AI on healthcare",
    "crew_mode": "sequential",
    "status": "completed",
    "result": "# AI in Healthcare Report\n\n## Executive Summary\n...",
    "error": null,
    "created_at": "2025-01-15T10:30:00Z",
    "completed_at": "2025-01-15T10:31:15Z"
}
```

### `TaskSummary`

```python
class TaskSummary(BaseModel):
    """Lightweight task summary for list endpoints."""

    task_id: str
    topic: str
    crew_mode: CrewMode
    status: TaskStatus
    created_at: datetime

    model_config = ConfigDict(use_enum_values=True)
```

Used by `GET /v1/tasks` to return a list without full result bodies.

### `HealthStatus`

```python
class HealthStatus(BaseModel):
    """Response for GET /health."""

    status: str = "healthy"
    components: dict[str, str] = Field(default_factory=dict)
```

**Example JSON:**

```json
{
    "status": "healthy",
    "components": {
        "llm_provider": "ok",
        "task_store": "ok",
        "websocket_manager": "ok"
    }
}
```

---

## Event Models

### `AgentEvent`

```python
class AgentEvent(BaseModel):
    """Real-time event streamed via WebSocket."""

    task_id: str
    event_type: EventType
    agent_role: AgentRole | None = None
    data: dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    model_config = ConfigDict(use_enum_values=True)
```

**Example — agent thinking:**

```json
{
    "task_id": "550e8400-...",
    "event_type": "agent_thinking",
    "agent_role": "researcher",
    "data": {
        "thought": "I need to find recent studies on AI in healthcare..."
    },
    "timestamp": "2025-01-15T10:30:05Z"
}
```

**Example — task completed:**

```json
{
    "task_id": "550e8400-...",
    "event_type": "task_completed",
    "agent_role": null,
    "data": {
        "result": "# Final Report\n\n..."
    },
    "timestamp": "2025-01-15T10:31:15Z"
}
```

**Serialization note:** `model_dump(mode="json")` is used for WebSocket transmission, which converts enums to string values and datetime to ISO 8601.

---

## Settings

### `Settings`

```python
class Settings(BaseSettings):
    """Application configuration loaded from environment."""

    # Application
    app_name: str = "ai-multi-agent"
    app_environment: AppEnvironment = AppEnvironment.LOCAL
    cloud_provider: CloudProvider = CloudProvider.LOCAL
    debug: bool = False

    # LLM
    llm_model: str = "llama3.2"
    llm_temperature: float = 0.7
    llm_max_tokens: int = 4096

    # AWS Bedrock
    aws_region: str = "us-east-1"
    aws_bedrock_model_id: str = "anthropic.claude-3-sonnet-20240229-v1:0"

    # Azure OpenAI
    azure_openai_endpoint: str = ""
    azure_openai_api_key: str = ""
    azure_openai_deployment: str = ""
    azure_openai_api_version: str = "2024-02-01"

    # Ollama
    ollama_base_url: str = "http://localhost:11434"

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # PostgreSQL
    postgres_url: str = "postgresql://postgres:postgres@localhost:5432/multiagent"

    # WebSocket
    ws_heartbeat_interval: int = 30

    # Frontend
    frontend_url: str = "http://localhost:3000"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )
```

### Environment Variable Mapping

| Setting | Env Var | Default |
|---------|---------|---------|
| `cloud_provider` | `CLOUD_PROVIDER` | `local` |
| `llm_model` | `LLM_MODEL` | `llama3.2` |
| `llm_temperature` | `LLM_TEMPERATURE` | `0.7` |
| `llm_max_tokens` | `LLM_MAX_TOKENS` | `4096` |
| `aws_region` | `AWS_REGION` | `us-east-1` |
| `aws_bedrock_model_id` | `AWS_BEDROCK_MODEL_ID` | `anthropic.claude-3-sonnet-...` |
| `azure_openai_endpoint` | `AZURE_OPENAI_ENDPOINT` | `""` |
| `azure_openai_api_key` | `AZURE_OPENAI_API_KEY` | `""` |
| `ollama_base_url` | `OLLAMA_BASE_URL` | `http://localhost:11434` |
| `redis_url` | `REDIS_URL` | `redis://localhost:6379/0` |
| `postgres_url` | `POSTGRES_URL` | `postgresql://postgres:...` |
| `frontend_url` | `FRONTEND_URL` | `http://localhost:3000` |

---

## Serialization Examples

### TaskRequest → JSON (API input)

```python
request = TaskRequest(topic="AI trends", crew_mode=CrewMode.SEQUENTIAL)
print(request.model_dump_json(indent=2))
# {"topic": "AI trends", "crew_mode": "sequential"}
```

### TaskResult → JSON (API response)

```python
result = TaskResult(
    task_id="abc-123",
    topic="AI trends",
    crew_mode=CrewMode.SEQUENTIAL,
    status=TaskStatus.COMPLETED,
    result="Report content...",
    created_at=datetime.utcnow(),
    completed_at=datetime.utcnow(),
)
print(result.model_dump_json(indent=2))
```

### AgentEvent → JSON (WebSocket)

```python
event = AgentEvent(
    task_id="abc-123",
    event_type=EventType.AGENT_THINKING,
    agent_role=AgentRole.RESEARCHER,
    data={"thought": "Analyzing the topic..."},
)
# Used in WebSocketManager:
await websocket.send_json(event.model_dump(mode="json"))
```

---

**Related:** [Architecture](../architecture-and-design/architecture.md) · [CrewAI Deep Dive](../ai-engineering/crewai-deep-dive.md)
