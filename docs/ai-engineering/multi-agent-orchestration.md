# Multi-Agent Orchestration Deep Dive

> How CrewAI agents collaborate: sequential vs hierarchical, delegation, and real-time events

---

## CrewAI Fundamentals

CrewAI is a multi-agent framework that orchestrates specialized AI agents:

```python
# Agent = role + goal + backstory + LLM
agent = Agent(
    role="Senior Research Analyst",
    goal="Gather comprehensive information",
    backstory="Expert at finding relevant data...",
    llm=chat_model,
    verbose=True,
)

# Task = description + expected_output + agent
task = Task(
    description="Research the topic: AI trends",
    expected_output="Structured research report",
    agent=agent,
)

# Crew = agents + tasks + process
crew = Crew(
    agents=[researcher, analyst, writer, critic],
    tasks=[research_task, analysis_task, writing_task, review_task],
    process="sequential",
)

result = crew.kickoff()
```

---

## Sequential Orchestration

```
Researcher → Analyst → Writer → Critic → Final Output
   (1)         (2)       (3)      (4)
```

Each agent receives the output of the previous agent as context:

1. **Researcher** → Research report (facts, sources)
2. **Analyst** → Analysis (patterns, insights) + research context
3. **Writer** → Polished report + analysis + research context
4. **Critic** → Review + feedback or approval

### When to Use Sequential

- Tasks with clear input → output chains
- Each agent builds on the previous
- Predictable execution time
- Simpler debugging

---

## Hierarchical Orchestration

```
         ┌── Manager Agent ──┐
         │                    │
    ┌────▼────┐         ┌────▼────┐
    │Researcher│         │ Analyst │
    └────┬────┘         └────┬────┘
         │                    │
    ┌────▼────┐         ┌────▼────┐
    │  Writer │◄────────│  Critic │
    └─────────┘ revise  └─────────┘
```

A manager agent dynamically delegates tasks:

- Can assign tasks to any agent
- Critic can send work **back** to Writer for revisions
- More adaptive but less predictable
- Higher token usage (manager reasoning overhead)

### When to Use Hierarchical

- Complex tasks requiring iteration
- Quality matters more than speed
- Feedback loops are important

---

## Agent Design Principles

### 1. Role Clarity

Each agent has a distinct specialty:

```python
Agent(
    role="Senior Research Analyst",  # Who they are
    goal="Gather comprehensive...",   # What they optimize for
    backstory="Expert at finding...", # Context for behavior
)
```

The LLM uses role + goal + backstory to shape its behavior.

### 2. Delegation Control

```python
# Researcher: can't delegate (produces input)
Agent(allow_delegation=False)

# Critic: can delegate (sends work back)
Agent(allow_delegation=True)
```

### 3. Iteration Limits

```python
Agent(max_iter=10)  # Safety valve per agent
```

Prevents infinite loops in hierarchical mode where agents can delegate back and forth.

---

## WebSocket Event Architecture

### Event Types

```python
class EventType(str, Enum):
    TASK_STARTED = "task_started"        # Crew begins
    AGENT_THINKING = "agent_thinking"    # Agent processing
    AGENT_ACTION = "agent_action"        # Agent tool use
    AGENT_RESULT = "agent_result"        # Agent output
    AGENT_DELEGATION = "agent_delegation" # Hierarchical delegation
    CREW_PROGRESS = "crew_progress"      # Overall progress
    TASK_COMPLETED = "task_completed"    # All done
    TASK_FAILED = "task_failed"          # Error
```

### Event Delivery

```
Backend → WebSocketManager.broadcast(event) →
  ├── global_connections (all clients)
  └── connections[task_id] (task-specific clients)
```

### Frontend Consumption

```typescript
const ws = new WebSocket("ws://localhost:8400/ws");
ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  // Render event with agent color + icon
};
```

---

## Comparison with AWS Services

| Multi-Agent Concept | AWS Equivalent | How |
|---------------------|---------------|-----|
| Sequential crew | Step Functions (sequential) | States execute in order |
| Hierarchical crew | Step Functions (parallel + choice) | Dynamic routing |
| Agent delegation | SNS → SQS | Message-based task assignment |
| WebSocket events | API Gateway WebSocket | Real-time push to clients |
| Task queue | SQS + Lambda | Async task processing |
| Background execution | Lambda async invoke | Fire-and-forget |
| Task persistence | DynamoDB | Durable task records |

---

## Performance Characteristics

| Mode | Agents | Typical Time | Token Usage |
|------|--------|-------------|-------------|
| Sequential (4 agents) | R→A→W→C | 30-90s | 4x single agent |
| Hierarchical (4 agents) | Dynamic | 45-120s | 5-7x single agent |
| Sequential (2 agents) | R→W | 15-45s | 2x single agent |

**Token usage scales linearly** with agents in sequential mode, and super-linearly in hierarchical (manager overhead).

---

**Related:** [Architecture](../architecture-and-design/architecture.md) · [Getting Started](../setup-and-tooling/getting-started.md)
