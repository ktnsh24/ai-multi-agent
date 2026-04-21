# Debugging Guide — ai-multi-agent

> Common issues, diagnostic commands, and troubleshooting steps for the multi-agent system

---

## Quick Diagnostics

```bash
# Check backend health
curl http://localhost:8400/health | python -m json.tool

# Check if services are running (Docker)
docker compose ps

# Backend logs
docker compose logs -f backend

# PostgreSQL connectivity
docker compose exec postgres psql -U postgres -c "SELECT 1"

# Redis connectivity
docker compose exec redis redis-cli ping
```

---

## Common Issues

### 1. CrewAI Agent Hangs or Times Out

**Symptoms**: Task stays in `running` status indefinitely. No WebSocket events after `task_started`.

**Causes**:
- Ollama not running or model not pulled
- LLM rate limiting (cloud providers)
- Agent stuck in reasoning loop

**Fix**:

```bash
# Check Ollama is running
curl http://localhost:11434/api/tags

# Pull the model if missing
ollama pull llama3.2

# Check agent max_iter setting
grep "max_iter" src/agents/definitions.py
```

If using cloud LLM, check credentials:

```bash
# AWS
aws sts get-caller-identity
aws bedrock-runtime invoke-model --model-id anthropic.claude-3-sonnet-20240229-v1:0 --body '{"prompt": "test"}' /dev/null

# Azure
echo $AZURE_OPENAI_ENDPOINT
echo $AZURE_OPENAI_API_KEY
```

### 2. WebSocket Connection Drops

**Symptoms**: Frontend shows "Disconnected". Events stop mid-execution.

**Causes**:
- Backend crashed during crew execution
- Network timeout (default is typically 60s)
- CORS blocking WebSocket upgrade

**Fix**:

```bash
# Check backend is still running
curl http://localhost:8400/health

# Check CORS settings in src/main.py
grep -A5 "CORSMiddleware" src/main.py

# Test WebSocket directly
python -c "
import asyncio, websockets
async def test():
    async with websockets.connect('ws://localhost:8400/ws') as ws:
        print('Connected!')
        await ws.send('{\"subscribe\": \"test\"}')
        msg = await asyncio.wait_for(ws.recv(), timeout=5)
        print(f'Received: {msg}')
asyncio.run(test())
"
```

### 3. Task Submission Returns 500

**Symptoms**: `POST /v1/tasks` returns Internal Server Error.

**Causes**:
- LLM provider not initialized
- Task store connection failed
- Missing environment variables

**Fix**:

```bash
# Check .env is loaded
poetry run python -c "from src.config import Settings; s = Settings(); print(s.cloud_provider)"

# Check required env vars
cat .env | grep -E "^(CLOUD_PROVIDER|LLM_|POSTGRES_|REDIS_)"

# Test task store directly
poetry run python -c "
import asyncio
from src.config import Settings
from src.tasks.store import create_task_store
async def test():
    s = Settings()
    store = await create_task_store(s)
    print(f'Store: {type(store).__name__}')
asyncio.run(test())
"
```

### 4. Frontend Can't Connect to Backend

**Symptoms**: "Network Error" in browser console. CORS errors.

**Causes**:
- Backend not running on expected port
- CORS not configured for frontend origin
- Docker networking issue

**Fix**:

```bash
# Check backend port
ss -tlnp | grep 8400

# Verify CORS allows frontend
grep "allow_origins" src/main.py

# In Docker, check networking
docker compose exec frontend curl http://backend:8400/health
```

### 5. PostgreSQL Connection Refused

**Symptoms**: Task store fails to initialize. Health check shows `task_store: error`.

**Causes**:
- PostgreSQL not running
- Wrong connection string
- Database not created

**Fix**:

```bash
# Check PostgreSQL is running
docker compose ps postgres

# Test connection
docker compose exec postgres psql -U postgres -l

# Check connection string
echo $POSTGRES_URL
# Expected: postgresql://postgres:postgres@localhost:5432/multiagent

# Create database if missing
docker compose exec postgres psql -U postgres -c "CREATE DATABASE multiagent"
```

### 6. Redis Connection Error

**Symptoms**: WebSocket manager can't broadcast. Caching fails.

**Fix**:

```bash
# Check Redis is running
docker compose ps redis
redis-cli -h localhost -p 6379 ping

# Check Redis URL
echo $REDIS_URL
# Expected: redis://localhost:6379/0
```

### 7. Agent Output Quality Issues

**Symptoms**: Agents produce generic or low-quality output.

**Causes**:
- Temperature too high (random outputs)
- Vague `expected_output` in task definition
- Small model (e.g., 7B) for complex tasks

**Fix**:

```bash
# Check LLM settings
grep -E "temperature|max_tokens|model" .env

# Recommended for quality:
# LLM_TEMPERATURE=0.3 (more focused)
# LLM_MAX_TOKENS=4096 (enough room for detailed output)
# LLM_MODEL=llama3.2 (or larger model)
```

Review task definitions in `src/agents/crew.py`:

```python
# ❌ Vague expected_output
expected_output="A good report"

# ✅ Specific expected_output
expected_output=(
    "A structured research report with: "
    "1. Executive summary, "
    "2. 5+ key findings with explanations, "
    "3. Data points and statistics, "
    "4. Sources and references"
)
```

---

## Debug Mode

### Enable Verbose Logging

```bash
# .env
LOG_LEVEL=DEBUG

# Or via command line
LOG_LEVEL=DEBUG poetry run uvicorn src.main:create_app --factory --port 8400
```

### CrewAI Verbose Mode

All agents are created with `verbose=True`, which logs their reasoning chain:

```
[Agent: Senior Research Analyst]
> Entering new AgentExecutor chain...
> Thought: I need to find information about...
> Action: [tool_name]
> Observation: [tool_output]
> Thought: Based on what I found...
> Final Answer: [structured output]
```

### WebSocket Event Tracing

Add a middleware to log all WebSocket events:

```python
# Temporary debugging — add to src/websocket/manager.py
async def send_to_task(self, task_id: str, event: AgentEvent) -> None:
    import logging
    logger = logging.getLogger(__name__)
    logger.debug(
        "WS event: task=%s type=%s agent=%s",
        task_id, event.event_type, event.agent_role,
    )
    # ... rest of method
```

---

## Performance Profiling

### Measure Crew Execution Time

```python
import time

start = time.perf_counter()
result = crew.kickoff()
elapsed = time.perf_counter() - start
print(f"Crew completed in {elapsed:.1f}s")
```

### Token Usage Estimation

| Component | Approx Tokens |
|-----------|---------------|
| Agent role + goal + backstory | ~100 each |
| Task description + expected_output | ~200 each |
| Context from prior tasks | Cumulative |
| 4-agent sequential crew | ~8,000-15,000 total |
| 4-agent hierarchical crew | ~12,000-25,000 total |

### Memory Usage

```bash
# Monitor backend memory
docker stats ai-multi-agent-backend-1

# Python memory profiling
pip install memory-profiler
mprof run python labs/lab2_four_agents.py
mprof plot
```

---

## Test Debugging

### Run Tests with Verbose Output

```bash
# All tests
poetry run pytest -v

# Specific test file
poetry run pytest tests/test_api.py -v

# Specific test
poetry run pytest tests/test_task_store.py::test_create_task -v

# With print output
poetry run pytest -v -s

# Stop on first failure
poetry run pytest -x
```

### Common Test Failures

| Failure | Cause | Fix |
|---------|-------|-----|
| `ModuleNotFoundError` | Dependencies not installed | `poetry install` |
| `ConnectionRefusedError` | Service not running | Start required services |
| `AssertionError: status != completed` | Async timing | Increase poll timeout |
| `WebSocketDisconnect` | Server not accepting connections | Check port binding |

---

## Log Locations

| Service | Location |
|---------|----------|
| Backend (local) | Terminal stdout |
| Backend (Docker) | `docker compose logs backend` |
| Frontend (local) | Terminal stdout + browser console |
| Frontend (Docker) | `docker compose logs frontend` |
| PostgreSQL | `docker compose logs postgres` |
| Redis | `docker compose logs redis` |

---

**Related:** [Getting Started](getting-started.md) · [Architecture](../architecture-and-design/architecture.md)
