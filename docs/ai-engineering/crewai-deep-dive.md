# CrewAI Deep Dive

> Understanding CrewAI's agent-task-crew model and how it powers multi-agent collaboration

---

## Table of Contents

1. [Why CrewAI](#why-crewai)
2. [Core Concepts](#core-concepts)
3. [Agent Definition](#agent-definition)
4. [Task Design](#task-design)
5. [Crew Orchestration](#crew-orchestration)
6. [Callbacks and Events](#callbacks-and-events)
7. [LLM Integration via Strategy Pattern](#llm-integration-via-strategy-pattern)
8. [Error Handling and Retries](#error-handling-and-retries)
9. [Certification Relevance](#certification-relevance)

---

## Why CrewAI

### Decision: CrewAI vs AutoGen vs LangGraph Multi-Agent

| Criteria | CrewAI | AutoGen | LangGraph |
|----------|--------|---------|-----------|
| **Abstraction level** | High (role-based) | Medium (conversation) | Low (graph nodes) |
| **Learning curve** | Low | Medium | High |
| **Role definition** | Built-in Agent class | Custom agent setup | Manual node design |
| **Process modes** | Sequential + Hierarchical | Conversation-based | Custom graph topology |
| **Delegation** | Built-in | Manual | Manual |
| **Python-native** | ✅ | ✅ | ✅ |
| **Production readiness** | Growing | Microsoft-backed | LangChain ecosystem |

**We chose CrewAI** because:

1. **Role-based abstraction** matches real-world team metaphors (researcher, analyst, writer, critic)
2. **Built-in process modes** (sequential/hierarchical) without writing graph logic
3. **Delegation mechanism** lets agents route work to specialists
4. **Simple mental model**: Agent + Task + Crew = orchestrated output
5. **LangChain compatibility**: Uses LangChain's LLM interfaces under the hood

---

## Core Concepts

```
┌─────────────────────────────────────────┐
│                  Crew                    │
│  ┌───────────┐  ┌───────────┐          │
│  │  Agent 1   │  │  Agent 2   │  ...    │
│  │ (Researcher)│  │ (Analyst)  │          │
│  └─────┬─────┘  └─────┬─────┘          │
│        │               │                │
│  ┌─────▼─────┐  ┌─────▼─────┐          │
│  │  Task 1    │  │  Task 2    │  ...    │
│  │ (Research) │  │ (Analyze)  │          │
│  └───────────┘  └───────────┘          │
│                                         │
│  Process: sequential | hierarchical     │
└─────────────────────────────────────────┘
```

### The Trinity

- **Agent** — A persona with role, goal, backstory, and optional tools
- **Task** — A unit of work with description, expected output, and assigned agent
- **Crew** — The orchestrator that runs agents through tasks in a given process

---

## Agent Definition

### Our Four Agents

From `src/agents/definitions.py`:

```python
def create_researcher(llm: BaseChatModel) -> Agent:
    """Research specialist — gathers raw information."""
    return Agent(
        role="Senior Research Analyst",
        goal="Gather comprehensive, accurate information on the given topic",
        backstory=(
            "You are an expert researcher with years of experience "
            "finding reliable sources and extracting key facts. "
            "You are thorough, methodical, and always cite your sources."
        ),
        llm=llm,
        verbose=True,
        allow_delegation=False,
        max_iter=15,
    )
```

### Key Parameters

| Parameter | Purpose | Our Default |
|-----------|---------|-------------|
| `role` | Who the agent is (shapes LLM behavior) | Unique per agent |
| `goal` | What the agent optimizes for | Task-specific |
| `backstory` | Context that influences reasoning style | Expertise narrative |
| `llm` | Language model instance | From strategy pattern |
| `verbose` | Log agent reasoning steps | `True` (for WebSocket events) |
| `allow_delegation` | Can delegate to other agents | `False` for most, `True` for critic |
| `max_iter` | Maximum reasoning iterations | `15` |
| `tools` | Optional tools the agent can use | `[]` (pure reasoning) |

### Role Design Guidelines

1. **Be specific**: "Senior Research Analyst" > "Researcher"
2. **Set clear goals**: "Gather comprehensive, accurate information" > "Do research"
3. **Backstory matters**: The LLM uses it to calibrate behavior
4. **Limit delegation**: Only enable for agents that need to send work back

### Agent Specialization

```
Researcher ──► Facts, sources, raw data
    │
Analyst ──────► Patterns, insights, comparisons
    │
Writer ───────► Polished, structured content
    │
Critic ───────► Quality review, feedback
```

Each agent sees the accumulated output of prior agents. The critic can:
- **Approve**: Task completes with final output
- **Revise** (hierarchical mode): Delegate back to writer for improvements

---

## Task Design

### Task Structure

```python
from crewai import Task

research_task = Task(
    description=f"Research the topic: {topic}. Find key facts, trends, and data.",
    expected_output="A structured research report with sections and citations.",
    agent=researcher,
)

analysis_task = Task(
    description="Analyze the research findings. Identify patterns and insights.",
    expected_output="An analysis report with key insights and recommendations.",
    agent=analyst,
    context=[research_task],  # Receives research output
)
```

### Context Chaining

In sequential mode, context flows automatically:

```
Task 1 output → Task 2 context → Task 3 context → Task 4 context
```

You can also explicitly set `context=[task1, task2]` for non-linear dependencies.

### Expected Output

The `expected_output` field is **critical** — it tells the agent what success looks like:

```python
# ❌ Vague
expected_output="A good report"

# ✅ Specific
expected_output=(
    "A structured research report with: "
    "1. Executive summary (3-5 sentences), "
    "2. Key findings (bullet points with sources), "
    "3. Data points and statistics, "
    "4. Recommendations for further investigation"
)
```

The LLM will shape its output to match this specification.

---

## Crew Orchestration

### Sequential Process

From `src/agents/crew.py`:

```python
async def run_sequential(
    self,
    topic: str,
    task_id: str,
) -> str:
    """Run agents in sequential order: researcher → analyst → writer → critic."""
    agents = create_all_agents(self.llm_provider.get_chat_model())
    researcher, analyst, writer, critic = agents

    # Create tasks in chain
    research_task = Task(
        description=f"Research the topic: {topic}",
        expected_output="Structured research report with key facts",
        agent=researcher,
    )
    analysis_task = Task(
        description="Analyze the research findings",
        expected_output="Analysis with patterns and insights",
        agent=analyst,
        context=[research_task],
    )
    writing_task = Task(
        description="Write a comprehensive report",
        expected_output="Polished report combining research and analysis",
        agent=writer,
        context=[research_task, analysis_task],
    )
    review_task = Task(
        description="Review and provide final assessment",
        expected_output="Final reviewed report with quality score",
        agent=critic,
        context=[research_task, analysis_task, writing_task],
    )

    crew = Crew(
        agents=[researcher, analyst, writer, critic],
        tasks=[research_task, analysis_task, writing_task, review_task],
        process=Process.sequential,
        verbose=True,
    )

    result = crew.kickoff()
    return str(result)
```

### Hierarchical Process

```python
async def run_hierarchical(
    self,
    topic: str,
    task_id: str,
) -> str:
    """Run with a manager agent that delegates dynamically."""
    agents = create_all_agents(self.llm_provider.get_chat_model())
    researcher, analyst, writer, critic = agents

    tasks = [
        Task(description=f"Research: {topic}", ...),
        Task(description="Analyze findings", ...),
        Task(description="Write report", ...),
        Task(description="Review quality", ...),
    ]

    crew = Crew(
        agents=[researcher, analyst, writer, critic],
        tasks=tasks,
        process=Process.hierarchical,
        manager_llm=self.llm_provider.get_chat_model(),
        verbose=True,
    )

    result = crew.kickoff()
    return str(result)
```

### Process Comparison

| Aspect | Sequential | Hierarchical |
|--------|-----------|--------------|
| **Execution order** | Fixed (task list order) | Dynamic (manager decides) |
| **Context passing** | Automatic chain | Manager routes context |
| **Delegation** | Not used | Core mechanism |
| **Manager agent** | None | Auto-created or custom |
| **Token usage** | Predictable (N agents) | Higher (manager overhead) |
| **Debugging** | Straightforward | Complex (dynamic routing) |
| **Best for** | Linear pipelines | Complex, iterative tasks |

---

## Callbacks and Events

### CrewAI Callback System

CrewAI supports callbacks that fire during execution:

```python
def step_callback(step_output):
    """Called after each agent step."""
    agent_name = step_output.agent
    action = step_output.action
    result = step_output.result

    # Emit WebSocket event
    event = AgentEvent(
        task_id=task_id,
        event_type=EventType.AGENT_ACTION,
        agent_role=agent_name,
        data={"action": action, "result": result},
        timestamp=datetime.utcnow(),
    )
    asyncio.create_task(ws_manager.send_to_task(task_id, event))
```

### Event Flow

```
CrewAI Agent Step
    │
    ▼
step_callback()
    │
    ▼
AgentEvent created
    │
    ▼
WebSocketManager.send_to_task()
    │
    ▼
Connected clients receive JSON
    │
    ▼
React UI updates in real-time
```

### Verbose Output Parsing

When `verbose=True`, CrewAI logs agent reasoning. We capture this for the WebSocket stream:

```
[Agent: Senior Research Analyst]
> Entering new AgentExecutor chain...
> Thought: I need to research AI trends for 2025
> Action: Search for recent publications
> Observation: Found 15 relevant articles
> Final Answer: [structured report]
```

Each line maps to an `EventType`:
- "Thought:" → `AGENT_THINKING`
- "Action:" → `AGENT_ACTION`
- "Observation:" → `AGENT_RESULT`
- "Final Answer:" → `AGENT_RESULT`

---

## LLM Integration via Strategy Pattern

### Why Strategy Pattern for Multi-Agent

Each agent in the crew uses the **same LLM instance**, but the strategy pattern lets us swap providers:

```python
# src/llm/provider.py
class BaseLLMProvider(ABC):
    @abstractmethod
    def get_chat_model(self) -> BaseChatModel:
        """Return a LangChain-compatible chat model."""
        ...

class OllamaProvider(BaseLLMProvider):
    def get_chat_model(self) -> BaseChatModel:
        return ChatOllama(model="llama3.2", temperature=0.7)

class BedrockProvider(BaseLLMProvider):
    def get_chat_model(self) -> BaseChatModel:
        return ChatBedrock(model_id="anthropic.claude-3-sonnet-...", ...)

class AzureOpenAIProvider(BaseLLMProvider):
    def get_chat_model(self) -> BaseChatModel:
        return AzureChatOpenAI(deployment_name=..., ...)
```

### Provider Selection

```python
def create_llm_provider(settings: Settings) -> BaseLLMProvider:
    match settings.cloud_provider:
        case CloudProvider.LOCAL:
            return OllamaProvider(settings)
        case CloudProvider.AWS:
            return BedrockProvider(settings)
        case CloudProvider.AZURE:
            return AzureOpenAIProvider(settings)
```

The **same crew definition** works across all three providers — only the LLM instance changes.

---

## Error Handling and Retries

### Agent-Level Errors

```python
try:
    result = crew.kickoff()
except Exception as e:
    # Update task status
    await task_store.update_status(task_id, TaskStatus.FAILED)

    # Emit error event via WebSocket
    error_event = AgentEvent(
        task_id=task_id,
        event_type=EventType.TASK_FAILED,
        data={"error": str(e)},
    )
    await ws_manager.send_to_task(task_id, error_event)
```

### Common Failure Modes

| Failure | Cause | Mitigation |
|---------|-------|------------|
| Token limit exceeded | Long context chain | Summarize between agents |
| Agent timeout | Slow LLM response | `max_iter` limit + timeout |
| Delegation loop | Agents delegating back and forth | `max_iter` per agent |
| Rate limiting | Too many LLM calls | Retry with exponential backoff |
| Invalid output | Agent produces unparseable result | `expected_output` clarity |

### Retry Strategy

```python
# CrewAI has built-in retry for LLM failures
crew = Crew(
    agents=agents,
    tasks=tasks,
    max_rpm=10,        # Rate limit: max 10 requests/minute
    max_retries=3,     # Retry failed LLM calls
)
```

---

## Certification Relevance

### AWS Certified Machine Learning — Specialty

- **Multi-agent patterns** → Understanding orchestration for complex AI workflows
- **Amazon Bedrock Agents** → AWS's managed multi-agent service (similar concepts)
- **Step Functions** → State machine orchestration (sequential/parallel) parallels crew processes

### AWS Certified Solutions Architect

- **Microservices orchestration** → CrewAI crews map to microservice coordination patterns
- **Event-driven architecture** → WebSocket events parallel SNS/SQS event routing
- **Async processing** → Background task execution maps to Lambda async invoke

### Azure AI Engineer Associate

- **Azure AI Agent Service** → Microsoft's multi-agent platform
- **Semantic Kernel** → Microsoft's agent framework (comparable to CrewAI)
- **Azure OpenAI** → LLM provider for agent reasoning

### Key Exam Concepts

1. **Agent specialization** = Single Responsibility Principle applied to AI
2. **Sequential processing** = Pipeline pattern (Step Functions, Azure Durable Functions)
3. **Hierarchical processing** = Orchestrator pattern (API Gateway + Lambda fan-out)
4. **Real-time events** = WebSocket/SSE push (API Gateway WebSocket, Azure Web PubSub)
5. **Task persistence** = Durable state (DynamoDB, Azure Cosmos DB)

---

**Related:** [Multi-Agent Orchestration](multi-agent-orchestration.md) · [WebSocket Deep Dive](websocket-deep-dive.md) · [Architecture](../architecture-and-design/architecture.md)
