# Hands-On Labs — Phase 2 (Labs 5–8)

> WebSocket events, REST API integration, React frontend, and Docker deployment

---

## Table of Contents

- [Lab 5: Real-Time WebSocket Events](#lab-5-real-time-websocket-events)
- [Lab 6: Full REST API Integration](#lab-6-full-rest-api-integration)
- [Lab 7: React Frontend Dashboard](#lab-7-react-frontend-dashboard)
- [Lab 8: Docker Compose Deployment](#lab-8-docker-compose-deployment)

---

## 🫏 The Donkey Analogy — Understanding Phase 2 Real-Time Orchestration

| Metric | 🫏 Donkey Analogy | What It Means for Multi-Agent | How It's Calculated |
|--------|-------------------|-------------------------------|---------------------|
| **WebSocket Events** | Live commentary channel — hear every play as it happens | Real-time agent events streamed to the frontend as they occur | Connect `ws://` → count event frames → verify agent-step events arrive in order |
| **REST API** | Official scoreboard of task status | Standard async task pattern: submit → poll → retrieve result | `POST /tasks` → `GET /tasks/{id}` → check status field + result payload |
| **Frontend Dashboard** | Audience view of events and results | User-facing UI showing live agent progress and final output | Load dashboard → verify WebSocket connection → check event rendering |
| **Docker Stack** | Recreates the same stadium anywhere | Multi-service deployment (orchestrator + agents + frontend + DB) | `docker compose up` → verify all services healthy → run end-to-end task |

---

## Lab 5: Real-Time WebSocket Events

### 🏢 Business Context

*"Stakeholders can't stare at a loading spinner for 60+ seconds. They need to see what each agent is doing in real-time — like watching a team collaborate live."*

### What You'll Build

Connect the `WebSocketManager` to CrewAI callbacks and stream `AgentEvent` objects to a WebSocket client.

### Steps

**Step 1: Create a WebSocket test client**

Create `labs/lab5_websocket_events.py`:

```python
"""Lab 5: WebSocket event streaming."""
import asyncio
import json
import websockets

async def listen_for_events():
    """Connect to WebSocket and display agent events."""
    uri = "ws://localhost:8400/ws"

    print("🔌 Connecting to WebSocket...")
    async with websockets.connect(uri) as ws:
        print("✅ Connected!")

        # Subscribe to a task (you'll need an active task_id)
        # For now, listen to all broadcast events
        print("👂 Listening for events...\n")

        try:
            async for message in ws:
                event = json.loads(message)
                event_type = event.get("event_type", "unknown")
                agent = event.get("agent_role", "system")
                data = event.get("data", {})

                # Color-coded output
                colors = {
                    "researcher": "\033[94m",   # Blue
                    "analyst": "\033[92m",      # Green
                    "writer": "\033[95m",       # Purple
                    "critic": "\033[93m",       # Yellow
                    "system": "\033[90m",       # Gray
                }
                reset = "\033[0m"
                color = colors.get(agent, "\033[0m")

                print(f"{color}[{agent}] {event_type}{reset}")
                if "thought" in data:
                    print(f"  💭 {data['thought'][:100]}")
                if "action" in data:
                    print(f"  ⚡ {data['action'][:100]}")
                if "result" in data:
                    print(f"  📄 {data['result'][:100]}")
                print()

        except websockets.ConnectionClosed:
            print("🔌 Connection closed")

if __name__ == "__main__":
    asyncio.run(listen_for_events())
```

**Step 2: Start the backend**

```bash
# Terminal 1: Start the FastAPI server
poetry run uvicorn src.main:create_app --factory --host 0.0.0.0 --port 8400 --reload
```

**Step 3: Run the WebSocket client**

```bash
# Terminal 2: Start the WebSocket listener
poetry run python labs/lab5_websocket_events.py
```

**Step 4: Submit a task via curl**

```bash
# Terminal 3: Submit a task
curl -X POST http://localhost:8400/v1/tasks \
  -H "Content-Type: application/json" \
  -d '{"topic": "AI trends 2025", "crew_mode": "sequential"}'
```

**Step 5: Watch events stream in Terminal 2**

You should see color-coded events from each agent as they process the task.

### Expected Output

```
🔌 Connecting to WebSocket...
✅ Connected!
👂 Listening for events...

[system] task_started
  📄 Task abc-123 started

[researcher] agent_thinking
  💭 I need to find recent information about AI trends...

[researcher] agent_result
  📄 Key findings: 1. LLMs continue to grow...

[analyst] agent_thinking
  💭 Analyzing the research findings for patterns...

[analyst] agent_result
  📄 Three major trends identified...

[writer] agent_thinking
  💭 Combining research and analysis into a report...

[critic] agent_result
  📄 Quality score: 8/10. Well-structured report...

[system] task_completed
  📄 Task abc-123 completed successfully
```

### Verify

- [ ] WebSocket client connects and receives events
- [ ] Events are tagged with agent_role and event_type
- [ ] Events arrive in real-time as agents execute
- [ ] Connection handles clean disconnect

### 🧠 Certification Question

- **AWS API Gateway WebSocket**: `$connect` / `$disconnect` / `$default` routes
- **Azure Web PubSub**: Hub → Group → Client subscription model
- **Concept**: Push-based event delivery vs polling

### What you learned

WebSocket events stream agent thoughts, actions, and results in real-time. Color-coded by agent role, they give full visibility into the multi-agent pipeline while it runs.

**✅ Skill unlocked:** You can consume WebSocket agent events and explain push vs poll.

---

## Lab 6: Full REST API Integration

### 🏢 Business Context

*"The WebSocket shows real-time events, but we also need standard REST endpoints for task management — submit, list, get by ID. The frontend team needs a predictable API contract."*

### What You'll Build

Test all REST API endpoints using `httpx` and verify task lifecycle.

### Steps

**Step 1: Create the API integration script**

Create `labs/lab6_rest_api.py`:

```python
"""Lab 6: Full REST API integration test."""
import asyncio
import httpx
import json

BASE_URL = "http://localhost:8400"

async def main():
    async with httpx.AsyncClient(base_url=BASE_URL, timeout=120.0) as client:
        # 1. Health check
        print("🏥 Health check...")
        resp = await client.get("/health")
        health = resp.json()
        print(f"   Status: {health['status']}")
        print(f"   Components: {json.dumps(health.get('components', {}), indent=2)}")
        print()

        # 2. Submit a task
        print("📤 Submitting task...")
        resp = await client.post("/v1/tasks", json={
            "topic": "Comparing AWS and Azure for AI workloads",
            "crew_mode": "sequential",
        })
        task = resp.json()
        task_id = task["task_id"]
        print(f"   Task ID: {task_id}")
        print(f"   Status: {task['status']}")
        print()

        # 3. Poll for completion
        print("⏳ Waiting for completion...")
        for attempt in range(30):
            await asyncio.sleep(5)
            resp = await client.get(f"/v1/tasks/{task_id}")
            task = resp.json()
            status = task["status"]
            print(f"   [{attempt+1}] Status: {status}")

            if status in ("completed", "failed"):
                break

        # 4. Get final result
        print(f"\n📄 Final task:")
        print(f"   ID: {task['task_id']}")
        print(f"   Topic: {task['topic']}")
        print(f"   Mode: {task['crew_mode']}")
        print(f"   Status: {task['status']}")
        if task.get("result"):
            print(f"   Result: {task['result'][:200]}...")
        print()

        # 5. List all tasks
        print("📋 All tasks:")
        resp = await client.get("/v1/tasks")
        tasks = resp.json()
        for t in tasks:
            print(f"   - {t['task_id'][:8]}... | {t['status']} | {t['topic']}")

if __name__ == "__main__":
    asyncio.run(main())
```

**Step 2: Run with the server running**

```bash
poetry run python labs/lab6_rest_api.py
```

### Expected Output

```
🏥 Health check...
   Status: healthy
   Components: {"llm": "ok", "task_store": "ok", "websocket": "ok"}

📤 Submitting task...
   Task ID: abc-123-...
   Status: pending

⏳ Waiting for completion...
   [1] Status: running
   [2] Status: running
   ...
   [8] Status: completed

📄 Final task:
   ID: abc-123-...
   Topic: Comparing AWS and Azure for AI workloads
   Mode: sequential
   Status: completed
   Result: # AWS vs Azure for AI Workloads...

📋 All tasks:
   - abc-123... | completed | Comparing AWS and Azure for AI workloads
```

### Verify

- [ ] Health endpoint returns component statuses
- [ ] Task submission returns task_id immediately
- [ ] Polling shows status progression (pending → running → completed)
- [ ] Final result contains structured agent output
- [ ] List endpoint returns all tasks

### 🧠 Certification Question

- **AWS**: API Gateway + Lambda async invoke pattern (submit → poll)
- **Azure**: Azure Functions with Durable Functions (orchestration status endpoint)
- **Concept**: Async task pattern: submit, poll, retrieve

### What you learned

The REST lifecycle — submit → poll → retrieve — is the standard async task pattern. The frontend team gets a predictable API contract independent of agent internals.

**✅ Skill unlocked:** You can test the full task lifecycle and explain the async pattern.

---

## Lab 7: React Frontend Dashboard

### 🏢 Business Context

*"The CLI tools are great for testing, but we need a web dashboard. Users should see a task form, real-time event stream, and final results — all in one page."*

### What You'll Build

Run and explore the Next.js frontend that connects to the FastAPI backend.

### Steps

**Step 1: Start the full stack**

```bash
# Terminal 1: Backend
cd repos/ai-multi-agent
poetry run uvicorn src.main:create_app --factory --host 0.0.0.0 --port 8400 --reload

# Terminal 2: Frontend
cd repos/ai-multi-agent/frontend
npm install
npm run dev
```

**Step 2: Open the dashboard**

Navigate to `http://localhost:3000` in your browser.

**Step 3: Submit a task**

1. Enter a topic: "Future of autonomous vehicles"
2. Select crew mode: Sequential
3. Click "Submit Task"

**Step 4: Watch the event stream**

The dashboard shows:
- **Task status** badge (pending → running → completed)
- **Agent event stream** — color-coded by agent role
- **Agent thinking** — real-time thought process
- **Final result** — formatted output when complete

**Step 5: Explore the React code**

Open `frontend/app/page.tsx` and examine:

```typescript
// WebSocket connection
const socket = new WebSocket("ws://localhost:8400/ws");

// Task submission
const response = await fetch("http://localhost:8400/v1/tasks", {
    method: "POST",
    body: JSON.stringify({ topic, crew_mode: crewMode }),
});

// Subscribe to task events
ws.send(JSON.stringify({ subscribe: task.task_id }));

// Render events with agent colors
const agentColors = {
    researcher: "text-blue-500",
    analyst: "text-green-500",
    writer: "text-purple-500",
    critic: "text-orange-500",
};
```

**Step 6: Test error handling**

1. Stop the backend server
2. Try submitting a task — observe error handling in the UI
3. Restart the backend — observe WebSocket reconnection

### Verify

- [ ] Frontend loads at `localhost:3000`
- [ ] Task submission creates a task via REST API
- [ ] WebSocket events stream in real-time
- [ ] Agent events are color-coded by role
- [ ] Final result displays when task completes

### 🧠 Certification Question

- **AWS Amplify**: Frontend hosting + API integration
- **Azure Static Web Apps**: React deployment with API backend
- **Concept**: Full-stack AI application with real-time updates

### What you learned

The React dashboard combines REST (task submission) and WebSocket (live events) in a single page. Agent events are color-coded and stream in real-time — the full user-facing experience.

**✅ Skill unlocked:** You can run and explore the full-stack frontend with real-time agent updates.

---

## Lab 8: Docker Compose Deployment

### 🏢 Business Context

*"Everything works locally, but we need to deploy as containers. Package the backend, frontend, Redis, and PostgreSQL into a single `docker compose up` command."*

### What You'll Build

Deploy the full stack using Docker Compose with all four services.

### Steps

**Step 1: Review the Docker Compose file**

```bash
cat docker-compose.yml
```

Key services:
- `backend` — FastAPI on port 8400
- `frontend` — Next.js on port 3000
- `redis` — Redis on port 6379
- `postgres` — PostgreSQL on port 5432

**Step 2: Build and start**

```bash
cd repos/ai-multi-agent
docker compose build
docker compose up -d
```

**Step 3: Check service health**

```bash
# All services running
docker compose ps

# Backend health
curl http://localhost:8400/health

# Frontend accessible
curl -s http://localhost:3000 | head -20
```

**Step 4: Submit a task via the containerized API**

```bash
curl -X POST http://localhost:8400/v1/tasks \
  -H "Content-Type: application/json" \
  -d '{"topic": "Container orchestration best practices", "crew_mode": "sequential"}'
```

**Step 5: View logs from each service**

```bash
# Backend logs (agent execution)
docker compose logs -f backend

# Frontend logs
docker compose logs -f frontend

# All services
docker compose logs -f
```

**Step 6: Clean up**

```bash
docker compose down -v  # -v removes volumes (database data)
```

### Expected Output

```
$ docker compose ps
NAME                    STATUS      PORTS
ai-multi-agent-backend-1   Up       0.0.0.0:8400->8400/tcp
ai-multi-agent-frontend-1  Up       0.0.0.0:3000->3000/tcp
ai-multi-agent-redis-1     Up       0.0.0.0:6379->6379/tcp
ai-multi-agent-postgres-1  Up       0.0.0.0:5432->5432/tcp
```

### Verify

- [ ] All four services start with `docker compose up`
- [ ] Backend health check passes
- [ ] Frontend accessible at `localhost:3000`
- [ ] Task submission works through containerized stack
- [ ] Services communicate via Docker network

### 🧠 Certification Question

- **AWS ECS**: Container orchestration (our Terraform deploys to Fargate)
- **Azure Container Apps**: Managed container platform
- **Docker Compose → ECS**: `docker compose` maps to ECS task definitions
- **Concept**: Container networking, service discovery, health checks

### What you learned

Four services (backend, frontend, Redis, PostgreSQL) start with one command. Docker networking handles inter-service communication. This Compose file is the blueprint for ECS/Container Apps.

**✅ Skill unlocked:** You can deploy the full multi-agent stack in Docker and verify all integrations.

---

## Phase 2 Labs — Skills Checklist

| # | Skill | Lab | Can you explain it? |
|---|---|---|---|
| 1 | WebSocket event streaming and agent callbacks | Lab 5 | [ ] Yes |
| 2 | REST task lifecycle (submit → poll → retrieve) | Lab 6 | [ ] Yes |
| 3 | Full-stack frontend + WebSocket integration | Lab 7 | [ ] Yes |
| 4 | Docker Compose multi-service deployment | Lab 8 | [ ] Yes |

---

**Previous:** [Hands-On Labs Phase 1](hands-on-labs-phase-1.md) · **Related:** [Getting Started](../setup-and-tooling/getting-started.md) · [Architecture](../architecture-and-design/architecture.md)
