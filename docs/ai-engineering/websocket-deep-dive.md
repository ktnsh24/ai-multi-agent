# WebSocket Deep Dive

> Real-time agent event streaming with FastAPI WebSocket, connection management, and React integration

---

## Table of Contents

1. [Why WebSocket for Multi-Agent](#why-websocket-for-multi-agent)
2. [FastAPI WebSocket Endpoint](#fastapi-websocket-endpoint)
3. [Connection Manager Pattern](#connection-manager-pattern)
4. [Event Protocol](#event-protocol)
5. [React Frontend Integration](#react-frontend-integration)
6. [Scaling WebSocket Connections](#scaling-websocket-connections)
7. [Error Handling and Reconnection](#error-handling-and-reconnection)
8. [Certification Relevance](#certification-relevance)

---

## Why WebSocket for Multi-Agent

### Decision: WebSocket vs SSE vs Polling

| Criteria | WebSocket | SSE | Polling |
|----------|-----------|-----|---------|
| **Direction** | Bidirectional | Server → Client | Client → Server |
| **Connection** | Persistent | Persistent | Repeated |
| **Latency** | ~0ms (push) | ~0ms (push) | Interval-dependent |
| **Client subscribe** | ✅ Send task_id | ❌ URL param only | ❌ Query param |
| **Binary data** | ✅ | ❌ | ✅ |
| **Browser support** | All modern | All modern | All |
| **Reconnection** | Manual | Auto (EventSource) | Built-in |

**We chose WebSocket** because:

1. **Bidirectional**: Client can subscribe to specific task_id after connecting
2. **Real-time events**: Agent thinking/action/result events need sub-second delivery
3. **Task subscription**: Client sends `{"subscribe": "task-123"}` to filter events
4. **Multi-agent context**: 4 agents × multiple steps = many events per task
5. **Phase 3 used SSE**: WebSocket demonstrates a different real-time pattern for the portfolio

---

## FastAPI WebSocket Endpoint

### Basic Setup

From `src/routes/ws.py`:

```python
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

router = APIRouter()

@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time agent events."""
    ws_manager: WebSocketManager = websocket.app.state.ws_manager
    task_id: str | None = None

    await ws_manager.connect(websocket)

    try:
        while True:
            data = await websocket.receive_json()

            # Client subscribes to a specific task
            if "subscribe" in data:
                task_id = data["subscribe"]
                await ws_manager.subscribe(websocket, task_id)
                await websocket.send_json({
                    "type": "subscribed",
                    "task_id": task_id,
                })

    except WebSocketDisconnect:
        await ws_manager.disconnect(websocket, task_id)
```

### Key Design Decisions

1. **No query parameters**: Client connects first, then subscribes via message
2. **JSON protocol**: All messages are JSON objects
3. **Subscription model**: Client can subscribe to one task at a time
4. **Graceful disconnect**: Cleanup on `WebSocketDisconnect` exception

---

## Connection Manager Pattern

### Architecture

```
WebSocketManager
├── global_connections: set[WebSocket]    # All connected clients
├── task_connections: dict[str, set[WebSocket]]  # task_id → clients
│
├── connect(ws)           # Add to global set
├── subscribe(ws, task_id) # Add to task-specific set
├── disconnect(ws, task_id) # Remove from all sets
├── broadcast(event)       # Send to ALL clients
├── send_to_task(task_id, event) # Send to task subscribers only
└── _safe_send(ws, data)   # Handle individual send errors
```

### Implementation

From `src/websocket/manager.py`:

```python
class WebSocketManager:
    """Manages WebSocket connections and event broadcasting."""

    def __init__(self) -> None:
        self._global_connections: set[WebSocket] = set()
        self._task_connections: dict[str, set[WebSocket]] = {}

    async def connect(self, websocket: WebSocket) -> None:
        """Accept and register a new WebSocket connection."""
        await websocket.accept()
        self._global_connections.add(websocket)

    async def subscribe(self, websocket: WebSocket, task_id: str) -> None:
        """Subscribe a connection to events for a specific task."""
        if task_id not in self._task_connections:
            self._task_connections[task_id] = set()
        self._task_connections[task_id].add(websocket)

    async def disconnect(
        self,
        websocket: WebSocket,
        task_id: str | None = None,
    ) -> None:
        """Remove a connection from all registries."""
        self._global_connections.discard(websocket)
        if task_id and task_id in self._task_connections:
            self._task_connections[task_id].discard(websocket)
            if not self._task_connections[task_id]:
                del self._task_connections[task_id]

    async def send_to_task(self, task_id: str, event: AgentEvent) -> None:
        """Send an event to all clients subscribed to a task."""
        connections = self._task_connections.get(task_id, set())
        data = event.model_dump(mode="json")

        disconnected: list[WebSocket] = []
        for ws in connections:
            try:
                await ws.send_json(data)
            except Exception:
                disconnected.append(ws)

        # Clean up dead connections
        for ws in disconnected:
            await self.disconnect(ws, task_id)

    async def broadcast(self, event: AgentEvent) -> None:
        """Send an event to ALL connected clients."""
        data = event.model_dump(mode="json")

        disconnected: list[WebSocket] = []
        for ws in self._global_connections:
            try:
                await ws.send_json(data)
            except Exception:
                disconnected.append(ws)

        for ws in disconnected:
            await self.disconnect(ws)
```

### Why `set` for Connections

- **O(1) add/remove**: Faster than list for connection management
- **No duplicates**: Prevents double-registration
- **Iteration safe**: Copy during broadcast to avoid mutation during iteration

### Dead Connection Cleanup

```python
# During send, catch failures and collect dead connections
disconnected: list[WebSocket] = []
for ws in connections:
    try:
        await ws.send_json(data)
    except Exception:
        disconnected.append(ws)

# Clean up AFTER iteration (don't modify set during iteration)
for ws in disconnected:
    await self.disconnect(ws, task_id)
```

---

## Event Protocol

### Message Types

#### Client → Server

```json
{
    "subscribe": "task-abc-123"
}
```

#### Server → Client (Subscription Confirmation)

```json
{
    "type": "subscribed",
    "task_id": "task-abc-123"
}
```

#### Server → Client (Agent Events)

```json
{
    "task_id": "task-abc-123",
    "event_type": "agent_thinking",
    "agent_role": "researcher",
    "data": {
        "thought": "I need to research AI trends..."
    },
    "timestamp": "2025-01-15T10:30:00Z"
}
```

### Event Type Lifecycle

```
task_started
    │
    ├── agent_thinking (researcher)
    ├── agent_action (researcher)
    ├── agent_result (researcher)
    │
    ├── agent_thinking (analyst)
    ├── agent_action (analyst)
    ├── agent_result (analyst)
    │
    ├── agent_thinking (writer)
    ├── agent_action (writer)
    ├── agent_result (writer)
    │
    ├── agent_thinking (critic)
    ├── agent_action (critic)
    ├── agent_result (critic)
    │
task_completed (with final result)
```

### Pydantic Event Model

From `src/models.py`:

```python
class AgentEvent(BaseModel):
    """Real-time event from agent execution."""

    task_id: str
    event_type: EventType
    agent_role: AgentRole | None = None
    data: dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    model_config = ConfigDict(use_enum_values=True)
```

Using `model_dump(mode="json")` ensures:
- Enums serialize to string values
- `datetime` serializes to ISO 8601
- Clean JSON for WebSocket transmission

---

## React Frontend Integration

### WebSocket Hook

From `frontend/app/page.tsx`:

```typescript
const [ws, setWs] = useState<WebSocket | null>(null);
const [events, setEvents] = useState<AgentEvent[]>([]);

// Connect on mount
useEffect(() => {
    const socket = new WebSocket("ws://localhost:8400/ws");

    socket.onopen = () => {
        console.log("WebSocket connected");
        setWs(socket);
    };

    socket.onmessage = (event) => {
        const data: AgentEvent = JSON.parse(event.data);
        setEvents((prev) => [...prev, data]);
    };

    socket.onclose = () => {
        console.log("WebSocket disconnected");
        setWs(null);
    };

    return () => socket.close();
}, []);
```

### Task Subscription

```typescript
const submitTask = async () => {
    // 1. Submit task via REST API
    const response = await fetch("http://localhost:8400/v1/tasks", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ topic, crew_mode: "sequential" }),
    });
    const task = await response.json();

    // 2. Subscribe to task events via WebSocket
    if (ws) {
        ws.send(JSON.stringify({ subscribe: task.task_id }));
    }
};
```

### Event Rendering

```typescript
// Color-code by agent role
const agentColors: Record<string, string> = {
    researcher: "text-blue-500",
    analyst: "text-green-500",
    writer: "text-purple-500",
    critic: "text-orange-500",
};

// Render event stream
{events.map((event, i) => (
    <div key={i} className={`p-2 ${agentColors[event.agent_role]}`}>
        <span className="font-bold">[{event.agent_role}]</span>
        <span className="text-gray-400 text-sm ml-2">
            {event.event_type}
        </span>
        <p className="mt-1">{JSON.stringify(event.data)}</p>
    </div>
))}
```

### Architecture Flow

```
React App (Next.js)
    │
    ├── POST /v1/tasks → FastAPI → Background task
    │                                    │
    ├── WebSocket /ws ←─── AgentEvents ──┘
    │       │
    │   subscribe(task_id)
    │       │
    └── Real-time UI updates
```

---

## Scaling WebSocket Connections

### Single Server (Our Setup)

```
Client A ──┐
Client B ──┼── WebSocketManager (in-memory) ── FastAPI
Client C ──┘
```

Works for development and small deployments.

### Multi-Server (Production)

```
Client A ── Server 1 ──┐
Client B ── Server 2 ──┼── Redis Pub/Sub
Client C ── Server 1 ──┘
```

For production with multiple backend instances:

```python
# Redis-backed WebSocket manager
class RedisWebSocketManager(WebSocketManager):
    """Extends WebSocketManager with Redis pub/sub for multi-server."""

    def __init__(self, redis_url: str) -> None:
        super().__init__()
        self._redis = Redis.from_url(redis_url)
        self._pubsub = self._redis.pubsub()

    async def send_to_task(self, task_id: str, event: AgentEvent) -> None:
        # Publish to Redis channel
        await self._redis.publish(
            f"task:{task_id}",
            event.model_dump_json(),
        )

    async def _listen(self) -> None:
        """Background task: listen for Redis messages and forward to local clients."""
        async for message in self._pubsub.listen():
            if message["type"] == "message":
                task_id = message["channel"].split(":")[1]
                data = json.loads(message["data"])
                # Forward to locally connected clients
                await super().send_to_task(task_id, AgentEvent(**data))
```

### Cloud WebSocket Services

| Service | Use Case |
|---------|----------|
| **AWS API Gateway WebSocket** | Managed WebSocket with Lambda backend |
| **AWS AppSync** | GraphQL subscriptions (WebSocket under the hood) |
| **Azure Web PubSub** | Managed WebSocket hub |
| **Azure SignalR** | Real-time messaging service |
| **Redis Pub/Sub** | Self-managed cross-server messaging |

---

## Error Handling and Reconnection

### Server-Side Error Handling

```python
async def _safe_send(self, ws: WebSocket, data: dict) -> bool:
    """Send data, return False if connection is dead."""
    try:
        await ws.send_json(data)
        return True
    except (WebSocketDisconnect, RuntimeError, ConnectionError):
        return False
```

### Client-Side Reconnection

```typescript
const MAX_RETRIES = 5;
const RETRY_DELAY = 1000; // ms

function connectWebSocket(retries = 0): WebSocket {
    const socket = new WebSocket("ws://localhost:8400/ws");

    socket.onclose = (event) => {
        if (!event.wasClean && retries < MAX_RETRIES) {
            setTimeout(() => {
                connectWebSocket(retries + 1);
            }, RETRY_DELAY * Math.pow(2, retries)); // Exponential backoff
        }
    };

    return socket;
}
```

### Heartbeat / Keep-Alive

```python
# Server sends periodic ping
async def _heartbeat(self, websocket: WebSocket) -> None:
    """Send periodic pings to detect dead connections."""
    while True:
        try:
            await websocket.send_json({"type": "ping"})
            await asyncio.sleep(30)
        except Exception:
            await self.disconnect(websocket)
            break
```

```typescript
// Client responds to pings
socket.onmessage = (event) => {
    const data = JSON.parse(event.data);
    if (data.type === "ping") {
        socket.send(JSON.stringify({ type: "pong" }));
        return;
    }
    // Handle normal events...
};
```

---

## Certification Relevance

### AWS API Gateway WebSocket API

- **Route selection**: `$connect`, `$disconnect`, `$default` routes → maps to our connect/disconnect/message handling
- **Integration**: Lambda backend processes messages → maps to our FastAPI handlers
- **Connection ID**: API Gateway tracks connections → maps to our `WebSocketManager` sets
- **DynamoDB for connections**: Store connection IDs for fan-out → maps to our `_task_connections` dict

### Azure Web PubSub / SignalR

- **Hub concept**: Centralized message broker → maps to our `WebSocketManager`
- **Groups**: Subscribe clients to groups → maps to our `task_connections` subscription
- **Upstream handlers**: Server-side message processing → maps to our WebSocket route

### Exam Questions Pattern

**Q**: "A multi-agent application needs to send real-time progress events to web clients. Each client should only receive events for their specific task. Which approach is most cost-effective?"

**A**: API Gateway WebSocket API with DynamoDB connection store + Lambda fan-out using task-based grouping.

**Our implementation**: `WebSocketManager` with `task_connections` dict demonstrates the exact same pattern at application level.

---

**Related:** [CrewAI Deep Dive](crewai-deep-dive.md) · [Multi-Agent Orchestration](multi-agent-orchestration.md) · [Architecture](../architecture-and-design/architecture.md)
