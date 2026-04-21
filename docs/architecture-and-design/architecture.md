# Architecture — AI Multi-Agent Platform

> Full-stack architecture: FastAPI + CrewAI + Next.js + WebSockets

---

## System Overview

```
                    ┌──────────────────┐
                    │  Next.js Frontend │
                    │  (port 3000)     │
                    └────┬────────┬────┘
                         │ HTTP   │ WebSocket
                    ┌────▼────────▼────┐
                    │  FastAPI Backend  │
                    │  (port 8400)     │
                    ├──────────────────┤
                    │  Route Layer     │
                    │  POST /v1/tasks  │
                    │  GET /v1/tasks   │
                    │  WS /ws          │
                    ├──────────────────┤
                    │  CrewAI Engine   │
                    │  Orchestrator    │
                    │  (seq/hier)      │
                    ├──────────────────┤
                    │  Agent Layer     │
                    │  Researcher      │
                    │  Analyst         │
                    │  Writer          │
                    │  Critic          │
                    ├──────────────────┤
                    │  LLM Provider    │
                    │  (Strategy)      │
                    └──┬──────────┬────┘
                       │          │
              ┌────────▼──┐  ┌───▼──────┐
              │  Redis     │  │  SQLite  │
              │  (pub/sub) │  │  (tasks) │
              └────────────┘  └──────────┘
```

---

## Component Details

### Frontend (Next.js)

- **Task Dashboard** — Submit tasks, select crew mode, choose agents
- **Agent Activity Stream** — Real-time WebSocket events with color-coded agents
- **Task History** — List of past tasks with status badges
- **Results Viewer** — Full agent outputs and final reports

### Backend (FastAPI)

- **Routes** — RESTful API for tasks + WebSocket for real-time events
- **CrewAI Orchestrator** — Manages agent collaboration (sequential/hierarchical)
- **Agent Definitions** — 4 agents with roles, goals, backstories
- **Task Store** — Persistence for task submissions and results
- **WebSocket Manager** — Broadcasts events to connected clients
- **LLM Provider** — Strategy pattern for AWS/Azure/Local

### Agents

| Agent | Capabilities | Delegation |
|-------|-------------|-----------|
| Researcher | Web search, document analysis | No (produces input) |
| Analyst | Pattern recognition, statistical thinking | No (processes input) |
| Writer | Content creation, formatting | No (produces output) |
| Critic | Quality review, feedback | Yes (can delegate back to Writer) |

### Data Flow

```
1. User submits task (HTTP POST)
2. Backend creates task record (SQLite)
3. Crew starts in background (BackgroundTasks)
4. Each agent processes sequentially:
   a. Agent thinks → WebSocket event (agent_thinking)
   b. Agent acts → WebSocket event (agent_action)
   c. Agent finishes → WebSocket event (agent_result)
   d. Output passes to next agent
5. Final result saved → WebSocket event (task_completed)
6. Frontend displays full result
```

---

## Design Patterns

### Strategy Pattern (LLM Providers)

```python
BaseLLMProvider (ABC)
  ├── BedrockProvider    → ChatBedrock
  ├── AzureOpenAIProvider → AzureChatOpenAI
  └── OllamaProvider     → ChatOllama
```

### Observer Pattern (WebSocket)

```python
WebSocketManager
  ├── global_connections    → receives all events
  └── connections[task_id]  → receives task-specific events
```

### Factory Pattern

```python
create_llm_provider(settings)   → BaseLLMProvider
create_task_store()             → BaseTaskStore
create_agent(role, llm)         → CrewAI Agent
```

### Background Tasks

```python
@router.post("/v1/tasks")
async def submit_task(request, background_tasks):
    task = await task_store.create(request)
    background_tasks.add_task(run_crew, task_id=task.task_id)
    return task  # Returns immediately
```

---

## Port Allocation

| Service | Port | Phase |
|---------|------|-------|
| RAG Chatbot | 8000 | Phase 1 |
| AI Gateway | 8100 | Phase 2 |
| AI Agent | 8200 | Phase 3 |
| MCP Server | 8300 | Phase 4 |
| **Multi-Agent Backend** | **8400** | **Phase 5** |
| **Multi-Agent Frontend** | **3000** | **Phase 5** |

---

**Next:** [Getting Started](../setup-and-tooling/getting-started.md)
