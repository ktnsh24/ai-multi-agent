# Testing Strategy & Inventory — AI Multi-Agent

> How the Multi-Agent Platform is tested — unit tests for task store and WebSocket manager, integration tests for the full task pipeline, and patterns for testing without CrewAI or real LLMs.

**Related:** [Architecture](../architecture-and-design/architecture.md) · [Getting Started](../setup-and-tooling/getting-started.md)

---

## Test Pyramid

```
        ╱ ╲           E2E (manual via curl + WebSocket client)
       ╱   ╲          Verify full stack with real Ollama + Next.js frontend
      ╱─────╲
     ╱       ╲        Integration (20 tests)
    ╱         ╲       Full pipeline: route → task store → crew → WebSocket
   ╱───────────╲
  ╱             ╲     Unit (23 tests)
 ╱               ╲    API routes, task store CRUD, WebSocket manager
╱─────────────────╲
```

---

## Running Tests

```bash
# All tests
poetry run pytest tests/ -v

# Integration tests only
poetry run pytest tests/test_integration.py -v

# With coverage
poetry run pytest tests/ --cov=src --cov-report=term-missing
```

---

## Test Inventory

### Unit Tests (3 files, ~23 tests)

| File | Tests | What it covers |
|---|---|---|
| `test_api.py` | 9 | Health, submit task, list/get/delete tasks, context, crew modes |
| `test_task_store.py` | 8 | InMemoryTaskStore: create, get, list, update, delete, context |
| `test_websocket.py` | 6 | WebSocketManager: connect, disconnect, broadcast, task-specific, cleanup |

### Integration Tests (1 file, 20 tests)

| File | Tests | What it covers |
|---|---|---|
| `test_integration.py` | 20 | Task submission, CRUD lifecycle, configuration, errors, health, WebSocket |

**Total: 4 files, ~43 tests**

---

## Test Patterns

### 1. Direct app.state Assignment

Components are set on `app.state` directly, bypassing the lifespan:

```python
app = create_app()
app.state.crew_orchestrator = MagicMock()
app.state.task_store = InMemoryTaskStore()
app.state.ws_manager = WebSocketManager()
```

### 2. Real In-Memory Implementations

`InMemoryTaskStore` and `WebSocketManager` are used without mocking — they work without external dependencies:

```python
@pytest.fixture
def task_store():
    return InMemoryTaskStore()
```

### 3. Background Task Testing

CrewAI runs as a FastAPI `BackgroundTask`. In tests, the crew orchestrator is mocked, so background tasks complete instantly without actually running agents.

### 4. Shared Fixtures (conftest.py)

`tests/conftest.py` provides:
- `mock_settings` — MagicMock with local provider
- `mock_crew_orchestrator` — MagicMock (no real CrewAI)
- `task_store` — Real InMemoryTaskStore
- `ws_manager` — Real WebSocketManager
- `app` / `client` — Fully wired test app + client

---

## Known Limitations

| Limitation | Why | Mitigation |
|---|---|---|
| CrewAI is mocked | Can't run real agent pipeline in CI | Mock returns realistic results |
| WebSocket E2E not tested | Requires async WebSocket client | Manual testing with frontend |
| No Next.js frontend tests | Separate frontend project | Frontend has its own test suite |
| Background tasks not awaited | FastAPI runs them after response | Task store updates verify completion |

---

## DE Parallel — What This Looks Like at Scale

| Layer | What | Tools |
|---|---|---|
| **Agent pipeline tests** | Test full CrewAI pipeline with real LLM | CrewAI test mode |
| **WebSocket tests** | Async WebSocket client testing | websockets library, pytest-asyncio |
| **Frontend E2E** | Next.js + WebSocket integration | Playwright, Cypress |
| **Load tests** | Multiple concurrent tasks + WS connections | Locust, k6 |
| **Monitoring tests** | Agent callbacks, event ordering | Custom event assertions |
