# AI Multi-Agent — CrewAI Orchestration with Real-Time Frontend

> **Phase 5** of the AI Engineering Portfolio — A multi-agent system built with CrewAI where specialized agents (Researcher → Analyst → Writer → Critic) collaborate on complex tasks, with a Next.js frontend showing real-time progress via WebSocket.

**Port:** 8400 (API) · 3000 (Frontend) · **Language:** Python 3.12 + TypeScript · **Framework:** FastAPI + CrewAI + Next.js

---

## Quick Links

### Getting Started

| Document | Description |
|---|---|
| [Getting Started](docs/setup-and-tooling/getting-started.md) | Prerequisites, installation, first run |
| [Debugging Guide](docs/setup-and-tooling/debugging-guide.md) | VS Code debugger setup for Python + TypeScript |

### Architecture & Design

| Document | Description |
|---|---|
| [Architecture Overview](docs/architecture-and-design/architecture.md) | System design, agent pipeline, WebSocket flow |

### AI Engineering

| Document | Description |
|---|---|
| [CrewAI Deep Dive](docs/ai-engineering/crewai-deep-dive.md) | Agent roles, tasks, sequential process |
| [Multi-Agent Orchestration Deep Dive](docs/ai-engineering/multi-agent-orchestration.md) | Orchestration strategies, delegation, quality gates |
| [WebSocket Deep Dive](docs/ai-engineering/websocket-deep-dive.md) | WebSocket events, frontend state management |
| [Cost Analysis](docs/ai-engineering/cost-analysis.md) | 4-agent token costs, AWS vs Azure, alternatives |

### Hands-On Labs

| Document | Description |
|---|---|
| [Phase 1 — Foundation](docs/hands-on-labs/hands-on-labs-phase-1.md) | Setup, first task, watching agents work |
| [Phase 2 — Advanced](docs/hands-on-labs/hands-on-labs-phase-2.md) | Custom agents, WebSocket integration |

### Testing & Reference

| Document | Description |
|---|---|
| [Testing Strategy & Inventory](docs/ai-engineering/testing.md) | All tests — unit, integration, E2E |

---

## What Does This Project Do?

A **multi-agent system** where 4 specialized AI agents collaborate on research tasks:

1. **You submit a task** → "Research quantum computing trends"
2. **Researcher** → searches the web, gathers sources
3. **Analyst** → structures findings, identifies patterns
4. **Writer** → produces a polished report
5. **Critic** → reviews for accuracy, suggests improvements
6. **Real-time updates** → WebSocket pushes each agent's progress to the frontend

```
Task Submission
    │
    ▼
┌─────────────────────────────────────┐
│  CrewAI Sequential Process          │
│                                     │
│  🔍 Researcher → 📊 Analyst        │──── WebSocket events
│       │              │              │     (real-time to frontend)
│       ▼              ▼              │
│  ✍️ Writer   →  🔎 Critic          │
│                      │              │
│                      ▼              │
│              Final Report           │
└─────────────────────────────────────┘
```

| Provider | LLM | Cost |
|---|---|---|
| **AWS** | Bedrock (Claude 3.5 Sonnet) | ~$0.003/1K tokens |
| **Azure** | Azure OpenAI (GPT-4o) | ~$0.0025/1K tokens |
| **Local** | Ollama (llama3.2) | **$0** |

---

## Advanced Features

| Feature | What it does | Pattern |
|---|---|---|
| **4-agent pipeline** | Researcher → Analyst → Writer → Critic | CrewAI sequential process |
| **Real-time WebSocket** | Live agent progress + task status updates | `WebSocketManager` broadcast |
| **Next.js frontend** | Dashboard showing agent activity, task history | React + TailwindCSS |
| **Task persistence** | SQLite storage for tasks and results | `BaseTaskStore` ABC |
| **Agent callbacks** | CrewAI callbacks emit WebSocket events | Event-driven architecture |
| **Quality gate** | Critic agent reviews and scores output | Multi-step validation |
| **Cloud LLM support** | AWS Bedrock + Azure OpenAI + Ollama | Strategy pattern |

---

## Project Structure

```
ai-multi-agent/
├── .github/workflows/          # CI/CD pipelines
├── docs/                       # Documentation (organised by topic)
│   ├── ai-engineering/         #   CrewAI, multi-agent patterns, real-time, testing
│   ├── architecture-and-design/#   Architecture overview
│   ├── hands-on-labs/          #   2 phases of guided labs
│   └── setup-and-tooling/      #   Getting started, debugging
├── infra/                      # Terraform (AWS + Azure)
├── src/                        # Python API source code
│   ├── config.py               #   Pydantic Settings (all env vars)
│   ├── main.py                 #   FastAPI factory + lifespan manager
│   ├── models.py               #   Request/response Pydantic models
│   ├── crew/                   #   CrewAI orchestration
│   │   ├── orchestrator.py     #   Crew setup, agent definitions, task pipeline
│   │   ├── agents.py           #   Agent role definitions (Researcher, Analyst, Writer, Critic)
│   │   └── tasks.py            #   Task definitions for each agent
│   ├── llm/                    #   LLM providers
│   │   └── provider.py         #   Bedrock, Azure OpenAI, Ollama (strategy pattern)
│   ├── storage/                #   Task persistence
│   │   └── task_store.py       #   SQLite / in-memory task store
│   ├── websocket/              #   Real-time communication
│   │   └── manager.py          #   WebSocket connection + broadcast manager
│   └── routes/                 #   API endpoints
│       ├── health.py           #   GET /health — component status
│       ├── tasks.py            #   POST /v1/tasks, GET /v1/tasks, GET /v1/tasks/{id}
│       └── websocket.py        #   WS /ws — real-time agent updates
├── frontend/                   # Next.js frontend
│   ├── src/
│   │   ├── app/                #   Next.js App Router pages
│   │   ├── components/         #   React components (TaskForm, AgentTimeline, etc.)
│   │   └── hooks/              #   Custom hooks (useWebSocket, useTask)
│   ├── package.json            #   npm dependencies
│   └── tailwind.config.ts      #   TailwindCSS configuration
├── tests/                      # Python tests
│   ├── test_api.py             #   Health, tasks, WebSocket tests
│   ├── test_crew.py            #   Orchestrator, agent pipeline tests
│   └── test_task_store.py      #   CRUD, persistence tests
├── pyproject.toml              # Poetry dependencies (Python API)
├── Dockerfile                  # Container image
├── docker-compose.yml          # Full stack: API + frontend + DB
└── .env.example                # Environment variable template
```

---

## API Endpoints

| Method | Path | Description |
|---|---|---|
| `POST` | `/v1/tasks` | Submit a new research task |
| `GET` | `/v1/tasks` | List all tasks with status |
| `GET` | `/v1/tasks/{id}` | Get task details + agent outputs |
| `DELETE` | `/v1/tasks/{id}` | Cancel / delete a task |
| `WS` | `/ws` | WebSocket — real-time agent progress events |
| `GET` | `/health` | Health check with component status |

### WebSocket Events

| Event | Payload | When |
|---|---|---|
| `task_started` | `{task_id, topic}` | Task begins processing |
| `agent_started` | `{task_id, agent_name, role}` | Agent begins work |
| `agent_progress` | `{task_id, agent_name, message}` | Agent working update |
| `agent_completed` | `{task_id, agent_name, output}` | Agent finishes |
| `task_completed` | `{task_id, result}` | All agents done |
| `task_failed` | `{task_id, error}` | Processing error |

---

## Quick Start

```bash
# 1. Install Ollama and pull model
curl -fsSL https://ollama.com/install.sh | sh
ollama pull llama3.2

# 2. Install Python dependencies
cd repos/ai-multi-agent && poetry install

# 3. Install frontend dependencies
cd frontend && npm install && cd ..

# 4. Configure
cp .env.example .env

# 5. Run API
poetry run start
# → http://localhost:8400/docs

# 6. Run frontend (separate terminal)
cd frontend && npm run dev
# → http://localhost:3000
```

```bash
# Submit a research task
curl -X POST http://localhost:8400/v1/tasks \
  -H "Content-Type: application/json" \
  -d '{"topic": "quantum computing trends 2024", "depth": "detailed"}'
```

See [Getting Started](docs/setup-and-tooling/getting-started.md) for the full step-by-step guide.

### Run on AWS or Azure

```bash
# Deploy + run all labs + destroy (automated)
./scripts/run_cloud_labs.sh --provider aws --email you@example.com

# Custom budget limit (default €5)
./scripts/run_cloud_labs.sh --provider aws --email you@example.com --cost-limit 15
```

Results saved to `scripts/lab_results/<aws|azure>/`.

---

## Tech Stack

| Layer | AWS | Azure | Local |
|---|---|---|---|
| **Language** | Python 3.12 + TypeScript | Python 3.12 + TypeScript | Python 3.12 + TypeScript |
| **Agent Framework** | CrewAI | CrewAI | CrewAI |
| **LLM** | Bedrock (Claude 3.5 Sonnet) | Azure OpenAI (GPT-4o) | Ollama (llama3.2) |
| **Task Store** | DynamoDB (planned) | Cosmos DB (planned) | SQLite / in-memory |
| **Frontend** | S3 + CloudFront | Static Web Apps | Next.js dev server |
| **Real-Time** | API Gateway WebSocket | Azure Web PubSub | FastAPI WebSocket |
| **Container** | ECS Fargate | Container Apps | Docker |

---

## Design Patterns

| Pattern | Where | Why |
|---|---|---|
| **Pipeline** | Researcher → Analyst → Writer → Critic | Sequential agent processing |
| **Strategy (ABC + Factory)** | `BaseLLMProvider`, `BaseTaskStore` | Swap providers |
| **Factory Method** | `create_llm_provider()`, `create_task_store()`, `create_crew_orchestrator()` | Single entry point |
| **Observer** | WebSocket manager + agent callbacks | Real-time event propagation |
| **Pub/Sub** | `WebSocketManager.broadcast()` | Multiple clients, one event source |
| **Role-Based Agents** | Each agent has a specific role + goal + backstory | Specialization |

---

## Documentation Structure

```
docs/
├── ai-engineering/                                ← Deep-dives + testing
│   ├── crewai-deep-dive.md                       ← Agent roles, tasks, process
│   ├── multi-agent-orchestration.md               ← Orchestration strategies
│   ├── websocket-deep-dive.md                    ← WebSocket events, frontend
│   ├── testing.md                                ← Test strategy & inventory
│   └── cost-analysis.md                          ← 4-agent token costs, alternatives
├── architecture-and-design/                      ← System design
│   └── architecture.md                           ← Architecture overview
├── hands-on-labs/                                ← Guided experiments
│   ├── hands-on-labs-phase-1.md                  ← Foundation: setup, first task
│   └── hands-on-labs-phase-2.md                  ← Advanced: custom agents, WS
└── setup-and-tooling/                            ← Getting started
    ├── getting-started.md                        ← Full setup guide
    └── debugging-guide.md                        ← Debugger setup
```

**Recommended reading order:**

1. [Architecture](docs/architecture-and-design/architecture.md) — how the agent pipeline works
2. [Getting Started](docs/setup-and-tooling/getting-started.md) — run it locally
3. [CrewAI Deep Dive](docs/ai-engineering/crewai-deep-dive.md) — agent roles and tasks
4. [WebSocket Deep Dive](docs/ai-engineering/websocket-deep-dive.md) — WebSocket integration

---

## Certification Relevance

| Multi-Agent Concept | AWS Service | Exam Relevance |
|---|---|---|
| Agent pipeline / orchestration | Step Functions | SAA-C03: workflow orchestration |
| Real-time WebSocket | API Gateway WebSocket | SAA-C03: real-time protocols |
| Task persistence | DynamoDB | SAA-C03: NoSQL design |
| Frontend hosting | S3 + CloudFront | SAA-C03: static hosting + CDN |
| Container orchestration | ECS Fargate | SAA-C03: compute services |
| Event-driven updates | EventBridge + SNS | SAA-C03: event-driven architecture |

---

**Phase:** Phase 5 (out of 5) · **Portfolio:** [Portfolio Overview](../../README.md)
