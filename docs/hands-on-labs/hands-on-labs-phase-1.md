# Hands-On Labs — Phase 1 (Labs 1–4)

> Build and test multi-agent orchestration from the ground up

---

## Table of Contents

- [Cost Estimation — Local vs Cloud](#cost-estimation--local-vs-cloud)
- [Lab 1: Your First CrewAI Crew](#lab-1-your-first-crewai-crew)
- [Lab 2: The Full Four-Agent Crew](#lab-2-the-full-four-agent-crew)
- [Lab 3: Connect to the Strategy Pattern LLM Provider](#lab-3-connect-to-the-strategy-pattern-llm-provider)
- [Lab 4: Task Persistence with the Store Pattern](#lab-4-task-persistence-with-the-store-pattern)

---

## Cost Estimation — Local vs Cloud

All labs run **locally for free**. Cloud costs if you deploy:

| Stack | Per lab session (~20 tasks) | Monthly (always on) | Best for |
|-------|-----------------------------|---------------------|----------|
| **Local (Ollama + CrewAI)** | $0 | $0 | Learning, experimenting |
| **AWS (cheapest)** | ~$0.10 | ~$25/mo (Fargate + DynamoDB) | Proving cloud skills |
| **Azure (cheapest)** | ~$0.05 | ~$5/mo (Container Apps + Cosmos DB free) | Best free tier |

> **Note:** Multi-agent pipelines make 4–8× more LLM calls per task than single-agent.
> Each agent (researcher, analyst, writer, reviewer) needs its own LLM invocations.
> Budget accordingly when using cloud LLM providers.

<details>
<summary>Detailed AWS breakdown</summary>

| Component | AWS Service | Cost |
|-----------|-------------|------|
| LLM (4 agents) | Bedrock (Claude 3 Haiku) | ~$0.10/session (4-8× calls) |
| Task store | DynamoDB (free tier) | $0 |
| API server | ECS Fargate (0.5 vCPU, 1GB) | ~$15/mo |
| WebSocket | API Gateway WebSocket | ~$1/mo |
| Frontend | S3 + CloudFront | ~$1/mo |
| Logs | CloudWatch | $0 (free tier) |

</details>

<details>
<summary>Detailed Azure breakdown</summary>

| Component | Azure Service | Cost |
|-----------|---------------|------|
| LLM (4 agents) | Azure OpenAI (GPT-4o mini) | ~$0.05/session |
| Task store | Cosmos DB (free tier: 1000 RU/s) | $0 |
| API server | Container Apps (free tier) | $0 |
| WebSocket | Container Apps (included) | $0 |
| Frontend | Static Web Apps (free tier) | $0 |
| Logs | Azure Monitor | $0 |

</details>

---

## 🚚 The Courier Analogy — Understanding Phase 1 Multi-Agent Flow

| Metric | 🚚 Courier Analogy | What It Means for Multi-Agent | How It's Calculated |
|--------|-------------------|-------------------------------|---------------------|
| **Agent Specialization** | Each courier has a role — researcher, analyst, writer, critic | Agents are purpose-built with specific system prompts and capabilities | Count distinct agent roles → verify each produces role-appropriate output |
| **Relay Handoff** | Researcher → Analyst → Writer → Critic pipeline | Output of one agent becomes input to the next in a defined sequence | Trace task through agent chain → verify context propagation at each step |
| **Quality Gate** | Reviewer courier inspects quality before release | Final agent scores/reviews output before it reaches the user | Critic agent returns score (1–10) → pass if score ≥ threshold |
| **Task Persistence** | Parcels are logged at each depot, not lost between stops | Async tasks survive restarts; status is queryable at any time | `POST /tasks` → `GET /tasks/{id}` → verify status transitions (pending → running → completed) |
| **Provider Abstraction** | Same relay route works on any road network | Swap LLM provider without changing agent definitions or flow | Change `CLOUD_PROVIDER` → re-run same task → verify equivalent quality |
| **Latency** | Total time for the relay team to complete the delivery | End-to-end time from task submission to final output | `completed_at − created_at` across all agent steps (ms) |

---

## Lab 1: Your First CrewAI Crew

### 🏢 Business Context

Your team lead asks: *"We need a research tool that uses multiple AI agents to analyze a topic. Start with a simple two-agent crew — one researches, one writes."*

### What You'll Build

A minimal CrewAI crew with two agents (researcher + writer) running in sequential mode.

### Prerequisites

- Python 3.11+ installed
- Poetry installed
- Ollama running with `llama3.2` model

### Steps

**Step 1: Set up the project**

```bash
cd repos/ai-multi-agent
poetry install
cp .env.example .env
# Edit .env: CLOUD_PROVIDER=local, LLM_MODEL=llama3.2
```

**Step 2: Create a standalone crew script**

Create `labs/lab1_first_crew.py`:

```python
"""Lab 1: Your first CrewAI crew."""
from crewai import Agent, Crew, Task, Process
from langchain_ollama import ChatOllama

# 1. Create the LLM
llm = ChatOllama(model="llama3.2", temperature=0.7)

# 2. Define agents
researcher = Agent(
    role="Research Analyst",
    goal="Find comprehensive information about the given topic",
    backstory="You are a thorough researcher who always cites sources.",
    llm=llm,
    verbose=True,
)

writer = Agent(
    role="Content Writer",
    goal="Write clear, engaging content based on research findings",
    backstory="You are a skilled writer who makes complex topics accessible.",
    llm=llm,
    verbose=True,
)

# 3. Define tasks
research_task = Task(
    description="Research the topic: 'Benefits of AI in healthcare'. Find key facts and statistics.",
    expected_output="A research report with 5+ key findings, each with a brief explanation.",
    agent=researcher,
)

writing_task = Task(
    description="Write a blog post based on the research findings.",
    expected_output="A 500-word blog post with introduction, body, and conclusion.",
    agent=writer,
    context=[research_task],
)

# 4. Create and run the crew
crew = Crew(
    agents=[researcher, writer],
    tasks=[research_task, writing_task],
    process=Process.sequential,
    verbose=True,
)

if __name__ == "__main__":
    print("🚀 Starting crew...")
    result = crew.kickoff()
    print("\n" + "=" * 60)
    print("📄 FINAL RESULT:")
    print("=" * 60)
    print(result)
```

**Step 3: Run the crew**

```bash
poetry run python labs/lab1_first_crew.py
```

**Step 4: Observe the output**

Watch the verbose output — you'll see:
- Researcher agent's thought process
- Research report passed to writer
- Writer agent crafting the blog post

### Expected Output

```
🚀 Starting crew...
[Agent: Research Analyst] > Entering new AgentExecutor chain...
> Thought: I need to research AI in healthcare...
> Final Answer: [research report]

[Agent: Content Writer] > Entering new AgentExecutor chain...
> Thought: Using the research findings, I'll write a blog post...
> Final Answer: [blog post]

============================================================
📄 FINAL RESULT:
============================================================
[A well-structured blog post about AI in healthcare]
```

### Verify

- [ ] Two agents created with distinct roles
- [ ] Research task output flows to writing task via `context`
- [ ] Sequential process completes both tasks
- [ ] Final output is a formatted blog post

### 🧠 Certification Question

- **AWS**: Amazon Bedrock Agents follow the same agent-task-tool model
- **Azure**: Semantic Kernel agents use similar role-based definitions
- **Concept**: Agent specialization = Single Responsibility Principle for AI

### What you learned

Two agents with distinct roles produce a result neither could alone. The `context` parameter passes output from researcher to writer — this is the sequential pipeline pattern.

**✅ Skill unlocked:** You can create a basic CrewAI crew and explain agent specialization.

---

## Lab 2: The Full Four-Agent Crew

### 🏢 Business Context

The research tool works, but stakeholders want *analysis* between research and writing, plus a *quality review* step: *"We can't publish without a reviewer checking the content."*

### What You'll Build

Extend to four agents: researcher → analyst → writer → critic, matching the production `src/agents/definitions.py`.

### Steps

**Step 1: Create the four-agent script**

Create `labs/lab2_four_agents.py`:

```python
"""Lab 2: Full four-agent crew."""
from crewai import Agent, Crew, Task, Process
from langchain_ollama import ChatOllama

llm = ChatOllama(model="llama3.2", temperature=0.7)

# Four specialized agents
researcher = Agent(
    role="Senior Research Analyst",
    goal="Gather comprehensive, accurate information on the given topic",
    backstory="Expert researcher who finds reliable sources and extracts key facts.",
    llm=llm, verbose=True, allow_delegation=False, max_iter=15,
)

analyst = Agent(
    role="Data Analyst",
    goal="Identify patterns, trends, and actionable insights from research",
    backstory="Analytical mind that finds hidden connections in data.",
    llm=llm, verbose=True, allow_delegation=False, max_iter=15,
)

writer = Agent(
    role="Technical Writer",
    goal="Create clear, well-structured reports combining research and analysis",
    backstory="Skilled writer who makes complex topics accessible.",
    llm=llm, verbose=True, allow_delegation=False, max_iter=15,
)

critic = Agent(
    role="Quality Reviewer",
    goal="Ensure accuracy, completeness, and clarity of the final report",
    backstory="Detail-oriented reviewer with high standards.",
    llm=llm, verbose=True, allow_delegation=False, max_iter=10,
)

# Task chain
topic = "The impact of large language models on software engineering"

research_task = Task(
    description=f"Research: {topic}. Find facts, statistics, and expert opinions.",
    expected_output="Research report: 5+ key findings with explanations and sources.",
    agent=researcher,
)

analysis_task = Task(
    description="Analyze the research findings. Identify 3+ patterns or trends.",
    expected_output="Analysis report: patterns, implications, and recommendations.",
    agent=analyst,
    context=[research_task],
)

writing_task = Task(
    description="Write a comprehensive report combining research and analysis.",
    expected_output="1000-word report: executive summary, findings, analysis, conclusion.",
    agent=writer,
    context=[research_task, analysis_task],
)

review_task = Task(
    description="Review the report for accuracy, completeness, and clarity. Score 1-10.",
    expected_output="Review: score (1-10), strengths, weaknesses, and specific improvements.",
    agent=critic,
    context=[research_task, analysis_task, writing_task],
)

crew = Crew(
    agents=[researcher, analyst, writer, critic],
    tasks=[research_task, analysis_task, writing_task, review_task],
    process=Process.sequential,
    verbose=True,
)

if __name__ == "__main__":
    print("🚀 Starting four-agent crew...")
    result = crew.kickoff()
    print("\n" + "=" * 60)
    print("📄 FINAL RESULT (with review):")
    print("=" * 60)
    print(result)
```

**Step 2: Run and compare**

```bash
poetry run python labs/lab2_four_agents.py
```

**Step 3: Compare with Lab 1**

Note the differences:
- Analyst adds a layer of insight between raw research and writing
- Critic provides quality scoring and feedback
- Context chain: each agent sees all prior work

### Expected Output

Four agent sections in verbose output, final result includes the critic's review with a quality score.

### Verify

- [ ] Four agents with distinct roles running sequentially
- [ ] Analyst adds insights not present in raw research
- [ ] Writer produces more structured output with analysis context
- [ ] Critic provides quality score and specific feedback

### 🧠 Certification Question

- **AWS Step Functions**: Sequential states = sequential crew process
- **Azure Durable Functions**: Function chaining pattern
- **Concept**: Pipeline pattern with quality gates

### What you learned

Four specialized agents form a pipeline with a quality gate (critic). The critic's score provides a measurable output quality signal — essential for production monitoring.

**✅ Skill unlocked:** You can build a four-agent pipeline and explain quality-gate patterns.

---

## Lab 3: Connect to the Strategy Pattern LLM Provider

### 🏢 Business Context

*"The local Ollama setup works for development, but we need to deploy to AWS with Bedrock and Azure with OpenAI. Use the same crew code for all three."*

### What You'll Build

Replace hard-coded `ChatOllama` with the strategy pattern `LLMProvider` from `src/llm/provider.py`.

### Steps

**Step 1: Create the provider-based script**

Create `labs/lab3_strategy_pattern.py`:

```python
"""Lab 3: CrewAI with strategy pattern LLM provider."""
import asyncio
from crewai import Agent, Crew, Task, Process

from src.config import Settings
from src.llm.provider import create_llm_provider

async def main():
    # 1. Load settings (reads .env)
    settings = Settings()
    print(f"☁️  Cloud provider: {settings.cloud_provider}")

    # 2. Create LLM provider via factory
    llm_provider = create_llm_provider(settings)
    chat_model = llm_provider.get_chat_model()
    print(f"🤖 LLM model: {settings.llm_model}")

    # 3. Create agents with the provider's chat model
    researcher = Agent(
        role="Research Analyst",
        goal="Find comprehensive information",
        backstory="Expert researcher.",
        llm=chat_model,
        verbose=True,
    )

    writer = Agent(
        role="Content Writer",
        goal="Write clear reports",
        backstory="Skilled technical writer.",
        llm=chat_model,
        verbose=True,
    )

    # 4. Run crew
    research_task = Task(
        description="Research: Cloud-native AI deployment patterns",
        expected_output="Report with 5+ key patterns.",
        agent=researcher,
    )

    writing_task = Task(
        description="Write a summary report.",
        expected_output="500-word summary.",
        agent=writer,
        context=[research_task],
    )

    crew = Crew(
        agents=[researcher, writer],
        tasks=[research_task, writing_task],
        process=Process.sequential,
        verbose=True,
    )

    result = crew.kickoff()
    print(f"\n📄 Result:\n{result}")

if __name__ == "__main__":
    asyncio.run(main())
```

**Step 2: Test with local provider**

```bash
# .env: CLOUD_PROVIDER=local
poetry run python labs/lab3_strategy_pattern.py
```

**Step 3: Test with AWS (if configured)**

```bash
# .env: CLOUD_PROVIDER=aws, AWS credentials configured
poetry run python labs/lab3_strategy_pattern.py
```

**Step 4: Observe the abstraction**

The crew code is **identical** regardless of provider. Only `.env` changes.

### Verify

- [ ] Same crew code runs with local Ollama
- [ ] Same crew code runs with AWS Bedrock (or would with credentials)
- [ ] Factory method selects provider based on `CLOUD_PROVIDER` env var
- [ ] No `if/else` in crew code — pure abstraction

### 🧠 Certification Question

- **AWS**: Amazon Bedrock supports multiple foundation models via unified API
- **Azure**: Azure OpenAI Service provides deployment abstraction
- **Design Pattern**: Strategy pattern = runtime algorithm selection (GoF)

### What you learned

The same crew code runs on Ollama, Bedrock, or Azure OpenAI. Only `.env` changes. The factory method selects the right provider at startup — zero conditional logic in the crew.

**✅ Skill unlocked:** You can switch LLM providers and explain the Strategy Pattern.

---

## Lab 4: Task Persistence with the Store Pattern

### 🏢 Business Context

*"Agent runs take 30-90 seconds. Users need to submit a task, close their browser, and come back later to see results. We need task persistence."*

### What You'll Build

Implement task submission and retrieval using the `TaskStore` from `src/tasks/store.py`.

### Steps

**Step 1: Create the persistence script**

Create `labs/lab4_task_store.py`:

```python
"""Lab 4: Task persistence with store pattern."""
import asyncio
import uuid
from datetime import datetime

from src.config import Settings
from src.models import TaskRequest, TaskResult, TaskStatus, CrewMode
from src.tasks.store import create_task_store

async def main():
    settings = Settings()

    # 1. Create task store (InMemory for local, Postgres for cloud)
    task_store = await create_task_store(settings)
    print(f"📦 Task store: {type(task_store).__name__}")

    # 2. Submit a task
    task_id = str(uuid.uuid4())
    request = TaskRequest(topic="AI in education", crew_mode=CrewMode.SEQUENTIAL)

    task_result = TaskResult(
        task_id=task_id,
        topic=request.topic,
        crew_mode=request.crew_mode,
        status=TaskStatus.PENDING,
        created_at=datetime.utcnow(),
    )

    await task_store.create(task_result)
    print(f"✅ Task created: {task_id}")

    # 3. Update status to running
    await task_store.update_status(task_id, TaskStatus.RUNNING)
    print(f"🔄 Task status: RUNNING")

    # 4. Simulate agent work
    print("⏳ Simulating crew execution...")
    await asyncio.sleep(2)

    # 5. Complete with result
    await task_store.update_result(
        task_id,
        result="AI is transforming education through personalized learning...",
        status=TaskStatus.COMPLETED,
    )
    print(f"✅ Task status: COMPLETED")

    # 6. Retrieve task
    stored_task = await task_store.get(task_id)
    print(f"\n📄 Retrieved task:")
    print(f"   ID: {stored_task.task_id}")
    print(f"   Topic: {stored_task.topic}")
    print(f"   Status: {stored_task.status}")
    print(f"   Result: {stored_task.result[:80]}...")

    # 7. List all tasks
    all_tasks = await task_store.list_tasks()
    print(f"\n📋 Total tasks: {len(all_tasks)}")

if __name__ == "__main__":
    asyncio.run(main())
```

**Step 2: Run with InMemoryTaskStore**

```bash
# .env: CLOUD_PROVIDER=local (uses InMemoryTaskStore)
poetry run python labs/lab4_task_store.py
```

**Step 3: Run with PostgresTaskStore (optional)**

```bash
# Start PostgreSQL
docker compose up -d postgres

# .env: CLOUD_PROVIDER=aws or azure (uses PostgresTaskStore)
poetry run python labs/lab4_task_store.py
```

### Expected Output

```
📦 Task store: InMemoryTaskStore
✅ Task created: abc-123-...
🔄 Task status: RUNNING
⏳ Simulating crew execution...
✅ Task status: COMPLETED

📄 Retrieved task:
   ID: abc-123-...
   Topic: AI in education
   Status: completed
   Result: AI is transforming education through personalized learning...

📋 Total tasks: 1
```

### Verify

- [ ] Task created with PENDING status
- [ ] Status transitions: PENDING → RUNNING → COMPLETED
- [ ] Task retrieved by ID with full result
- [ ] Same code works with InMemory and Postgres stores

### 🧠 Certification Question

- **AWS DynamoDB**: Task persistence with partition key = task_id
- **Azure Cosmos DB**: Document store for task records
- **Concept**: Strategy pattern for storage backends (same interface, different implementations)

### What you learned

Task persistence decouples submission from execution. Users submit, close their browser, and retrieve results later. The same TaskStore interface works with InMemory (dev) and PostgreSQL (prod).

**✅ Skill unlocked:** You can manage task lifecycle and explain the store abstraction.

## Phase 1 Labs — Skills Checklist

| # | Skill | Lab | Can you explain it? |
|---|---|---|---|
| 1 | Basic two-agent crew orchestration | Lab 1 | [ ] Yes |
| 2 | Four-agent pipeline and quality gate | Lab 2 | [ ] Yes |
| 3 | Strategy pattern for LLM providers | Lab 3 | [ ] Yes |
| 4 | Task store lifecycle and persistence | Lab 4 | [ ] Yes |

---

**Next:** [Hands-On Labs Phase 2](hands-on-labs-phase-2.md) (WebSocket events, REST API, Frontend, Docker)
