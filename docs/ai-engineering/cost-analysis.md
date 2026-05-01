# Cost Analysis — AI Multi-Agent

> Per-service cost breakdown for AWS, Azure, and Local — including the token multiplier effect of 4 sequential agents and WebSocket/frontend hosting costs.

**Related:** [Architecture](../architecture-and-design/architecture.md) · [CrewAI Deep Dive](crewai-deep-dive.md)

**Shared baseline:** [Cost Analysis Playbook (portfolio-level)](../../../../docs/shared/ai-engineering/cost-analysis-playbook.md)

## Table of Contents

- [Monthly Cost Summary](#monthly-cost-summary)
  - [Development (personal account)](#development-personal-account)
  - [Production (small scale)](#production-small-scale-100-tasksday)
- [Why Multi-Agent Costs 4× More Than Single Agent](#why-multi-agent-costs-4-more-than-single-agent)
- [Service-by-Service Breakdown](#service-by-service-breakdown)
  - [LLM Inference (via CrewAI)](#llm-inference-via-crewai)
  - [Task Store](#task-store)
  - [WebSocket (Real-Time Updates)](#websocket-real-time-updates)
  - [Frontend Hosting (Next.js)](#frontend-hosting-nextjs)
- [What Alternatives Cost More](#what-alternatives-cost-more)
- [Decision Summary](#decision-summary)
- [How to Minimise Costs on Personal Account](#how-to-minimise-costs-on-personal-account)
- [Cost of Running Tests on Cloud](#cost-of-running-tests-on-cloud)
- [Budget Guard — Automatic Cost Protection](#budget-guard--automatic-cost-protection)

---

## Monthly Cost Summary

### Development (personal account)

| Service | AWS Cost/month | Azure Cost/month | Notes |
|---|---|---|---|
| LLM (pay-per-use) | ~$5–15 | ~$5–15 | 4 agents × multi-turn = heavy token usage |
| Task Store | $0 (SQLite/in-memory) | $0 (SQLite/in-memory) | Local storage |
| WebSocket | $0 (local) | $0 (local) | FastAPI built-in |
| Frontend (Next.js) | $0 (local) | $0 (local) | `npm run dev` |
| Container Hosting | $0 (local) | $0 (local) | Run locally |
| **Total** | **~$5–15/month** | **~$5–15/month** | Most expensive repo due to 4-agent pipeline |

### Production (small scale: ~100 tasks/day)

| Service | AWS Cost/month | Azure Cost/month |
|---|---|---|
| LLM | ~$200–400 | ~$150–300 |
| Task Store | ~$5 (DynamoDB) | ~$5 (Cosmos DB) |
| WebSocket | Included in container | Included in container |
| Frontend Hosting | ~$5 (S3 + CloudFront) | ~$5 (Static Web Apps) |
| Container Hosting | ~$30 (Fargate) | ~$20 (Container Apps) |
| **Total** | **~$240–440/month** | **~$180–330/month** |

> **Key insight:** This is the most expensive repo in the portfolio. 4 agents × 3–5 LLM calls each = 12–20 LLM calls per task. Each task costs ~$0.15–0.40 on cloud.

---

## Why Multi-Agent Costs 4× More Than Single Agent

### Token Flow Through the Pipeline

```
Task: "Research quantum computing trends"

🔍 Researcher (3 LLM calls):
   Think → Search → Observe → Think → Search → Observe → Write findings
   Tokens: ~3000 (research context is verbose)

📊 Analyst (2 LLM calls):
   Read research → Identify patterns → Write analysis
   Tokens: ~2500 (input includes full research output)

✍️ Writer (2 LLM calls):
   Read analysis → Draft report → Revise
   Tokens: ~3000 (generates the longest output)

🔎 Critic (2 LLM calls):
   Read full report → Evaluate → Suggest improvements
   Tokens: ~2000 (input includes full report)
────────────────────────────────────────────────
Total: ~9 LLM calls, ~10,500 tokens
```

### Cost per Task by Provider

| Provider | LLM Calls | Total Tokens | Input Cost | Output Cost | Total |
|---|---|---|---|---|---|
| **Local (Ollama)** | ~9 | ~10,500 | $0 | $0 | **$0** |
| **AWS (Bedrock)** | ~9 | ~10,500 | ~$0.016 | ~$0.079 | **~$0.095** |
| **Azure (OpenAI)** | ~9 | ~10,500 | ~$0.013 | ~$0.053 | **~$0.066** |

### Cost Comparison Across Portfolio

| Phase | Repo | LLM Calls per Request | Cost per Request (AWS) |
|---|---|---|---|
| V1 | rag-chatbot | 1 | ~$0.013 |
| V2 | ai-gateway | 1 (+ cache savings) | ~$0.009 (with 30% cache) |
| V3 | ai-agent | 2–4 | ~$0.025 |
| V4 | mcp-server | 0 (tools only) | $0 |
| **V5** | **ai-multi-agent** | **9–20** | **~$0.095–0.40** |

---

## Service-by-Service Breakdown

### LLM Inference (via CrewAI)

CrewAI calls the LLM multiple times per agent. Token costs are the same per-call but multiply across agents:

| | AWS Bedrock (Claude 3.5 Sonnet) | Azure OpenAI (GPT-4o) | Local (Ollama) |
|---|---|---|---|
| **Per LLM call** | ~$0.013 | ~$0.010 | **$0** |
| **Per task (4 agents)** | ~$0.095 | ~$0.066 | **$0** |
| **100 tasks/day** | ~$285/month | ~$198/month | **$0** |

### Task Store

| Option | Cost/month | Persistence | Scales to zero? |
|---|---|---|---|
| **In-memory** | $0 | Restart = lost | N/A |
| **SQLite** | $0 | Local file | N/A |
| **AWS DynamoDB** | ~$0–5 | Yes | Yes (free tier) |
| **Azure Cosmos DB** | ~$0–5 | Yes | Yes (free tier) |

### WebSocket (Real-Time Updates)

| Option | Cost | Connections | Notes |
|---|---|---|---|
| **FastAPI built-in** | $0 (included) | ~100 concurrent | Good for development |
| **AWS API Gateway WebSocket** | ~$1/million messages | Unlimited | Production scale |
| **Azure Web PubSub** | ~$1/million messages | Unlimited | Production scale |

WebSocket costs are negligible — a task generates ~10 events, so 100 tasks/day = 1000 messages/day = ~$0.03/month.

### Frontend Hosting (Next.js)

| Option | Cost/month | CDN? | Custom domain? |
|---|---|---|---|
| **Local dev server** | $0 | No | No |
| **AWS S3 + CloudFront** | ~$1–5 | Yes | Yes |
| **Azure Static Web Apps** | $0 (free tier) | Yes | Yes |
| **Vercel (free tier)** | $0 | Yes | Yes |

**What we chose:**
- **Development:** `npm run dev` on localhost:3000
- **Production:** S3 + CloudFront or Azure Static Web Apps (both <$5/month)

---

## What Alternatives Cost More

### Alternative 1: AutoGen instead of CrewAI

| | CrewAI (our choice) | AutoGen |
|---|---|---|
| **Agent control** | Role-based, sequential | Conversation-based |
| **Token usage** | Controlled (sequential pipeline) | Higher (agents debate) |
| **Cost per task** | ~$0.10 (4 agents) | ~$0.20–0.50 (agents may loop) |
| **Max iterations** | Configurable per agent | Harder to limit |

**Why CrewAI is better:** Sequential pipeline gives predictable costs. AutoGen's conversational approach can lead to agents debating endlessly (= runaway token costs).

### Alternative 2: AWS Step Functions for Agent Orchestration

| | CrewAI + FastAPI (our choice) | Step Functions + Lambda |
|---|---|---|
| **Real-time updates** | WebSocket (instant) | Polling or EventBridge (delayed) |
| **Complexity** | Medium | High (state machines + Lambda per agent) |
| **Cost** | ~$30/month (Fargate) | ~$15/month (Lambda) + complexity |
| **Local development** | Yes (Ollama) | No (AWS only) |

**Why CrewAI is better:** WebSocket gives instant agent updates. Step Functions would require polling or EventBridge, adding latency and complexity.

### Alternative 3: LangGraph Multi-Agent instead of CrewAI

| | CrewAI (our choice) | LangGraph Multi-Agent |
|---|---|---|
| **Abstraction** | High (declarative roles) | Low (build graph manually) |
| **Agent definition** | Role + Goal + Backstory | Custom state graph nodes |
| **Learning value** | Shows orchestration patterns | Shows graph patterns |

**Why CrewAI for V5:** V3 already uses LangGraph for single-agent. Using CrewAI in V5 demonstrates a different framework and the portfolio shows breadth.

---

## Decision Summary

| Decision | Chosen | Alternative | Why chosen wins |
|---|---|---|---|
| Agent framework | CrewAI | AutoGen / LangGraph multi-agent | Predictable costs, role-based, different from V3 |
| Frontend | Next.js | React SPA / Streamlit | Modern SSR, WebSocket integration, portfolio breadth |
| Real-time | FastAPI WebSocket | Polling / SSE | Instant updates, bidirectional |
| Task store | SQLite / In-memory | PostgreSQL | Zero setup for development |
| Hosting | Fargate / Container Apps | EKS / AKS | Simpler, cheaper for single service |

---

## How to Minimise Costs on Personal Account

1. **Use Ollama for ALL development** — 4-agent tasks cost $0.10–0.40 on cloud but $0 locally
2. **Reduce agent count** — Test with 2 agents (researcher + writer) instead of 4
3. **Lower `max_iterations`** — Default 15 per agent; set to 5 for cost-conscious testing
4. **Use in-memory task store** — No cloud database needed
5. **Run frontend locally** — No hosting costs during development
6. **Set billing alerts** — $10/month budget (this repo can spend fast with 4 agents)

---

## Cost of Running Tests on Cloud

| Provider | Tasks | LLM Calls | Token Cost | Total per Run |
|---|---|---|---|---|
| **Local (Ollama)** | ~10 | ~90 | $0 | **$0** |
| **AWS (Bedrock)** | ~10 | ~90 | ~$0.95 | **~$0.95** |
| **Azure (OpenAI)** | ~10 | ~90 | ~$0.66 | **~$0.66** |

> **⚠️ This is the most expensive repo to test on cloud.** Each task triggers 4 agents × ~2 LLM calls = ~9 calls. **Always run locally first.** One cloud run for verification costs ~$1.

---

## Budget Guard — Automatic Cost Protection

Both `infra/aws/` and `infra/azure/` include a **budget guard** (`budget.tf`) that automatically protects against runaway cloud costs.

### How it works

| Threshold | Action |
|---|---|
| **80% of limit (€4)** | Email warning sent to `alert_email` |
| **100% of limit (€5)** | Email + automatic resource kill switch triggered |

### AWS

- **AWS Budget** monitors tagged resources (`service=ai-multi-agent`)
- **SNS → Lambda** pipeline: at 100%, a Lambda function scales ECS to 0 and cleans up ElastiCache
- File: `infra/aws/budget.tf` + `infra/aws/budget_killer_lambda/handler.py`

### Azure

- **Azure Consumption Budget** scoped to the resource group
- **Action Group → Automation Runbook**: at 100%, a PowerShell runbook deletes all resources in the resource group
- File: `infra/azure/budget.tf`

### Configuration

```hcl
variable "cost_limit_eur" {
  default = 5  # €5 kill switch
}

variable "alert_email" {
  # Required — where budget warnings go
}
```

### ⚠️ Important caveat

Cloud cost reporting has a **6–24 hour lag**. The budget guard is your **safety net**, not your primary defense. Always run:

```bash
terraform destroy  # immediately after finishing labs
```
