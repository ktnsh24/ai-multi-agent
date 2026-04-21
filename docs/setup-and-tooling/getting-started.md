# Getting Started — AI Multi-Agent Platform

> **Time to first task result:** ~10 minutes (local) | ~25 minutes (cloud deployment)

---

## Table of Contents

- [What you need before starting](#what-you-need-before-starting)
- [Step 1 — Install Python 3.11 and Poetry](#step-1--install-python-311-and-poetry)
- [Step 2 — Install Node.js 20+](#step-2--install-nodejs-20)
- [Step 3 — Clone and install dependencies](#step-3--clone-and-install-dependencies)
- [Step 4 — Configure environment variables](#step-4--configure-environment-variables)
- [Step 5 — Start the platform (local)](#step-5--start-the-platform-local)
- [Step 6 — Submit your first task](#step-6--submit-your-first-task)
- [Step 7 — WebSocket testing](#step-7--websocket-testing)
- [Step 8 — Docker (full stack)](#step-8--docker-full-stack)
- [Step 9 — Run Labs Locally](#step-9--run-labs-locally)
- [Step 10 — Connect to AWS (and run on AWS)](#step-10--connect-to-aws-and-run-on-aws)
- [Step 11 — Connect to Azure (and run on Azure)](#step-11--connect-to-azure-and-run-on-azure)
- [Step 12 — Run the Tests](#step-12--run-the-tests)
- [Step 13 — Project Structure](#step-13--project-structure)
- [Troubleshooting](#troubleshooting)

---

## What you need before starting

| Tool | Version | Why you need it |
| --- | --- | --- |
| **Python** | 3.11+ | Backend is written in Python |
| **Poetry** | 1.8+ | Python package manager |
| **Node.js** | 20+ | Frontend is written in TypeScript/React |
| **npm** | 10+ | Frontend package manager (bundled with Node.js) |
| **Git** | 2.40+ | Version control |
| **Ollama** | Latest | Local LLM (for `CLOUD_PROVIDER=local`) |
| **Docker** | 24+ | Optional — run full stack with one command |
| **AWS CLI** | 2.x | Connect to AWS services (optional) |
| **Azure CLI** | 2.x | Connect to Azure services (optional) |
| **Terraform** | 1.5+ | Deploy cloud infrastructure (optional) |

### Check what is already installed

```bash
python3 --version      # Need 3.11+
poetry --version       # Need 1.8+
node --version         # Need 20+
npm --version          # Need 10+
git --version          # Need 2.40+
ollama --version       # Need latest
docker --version       # Optional
aws --version          # Optional
az --version           # Optional
terraform --version    # Optional
```

---

## Step 1 — Install Python 3.11 and Poetry

```bash
# Ubuntu / WSL — Python
sudo apt update
sudo apt install -y python3.11 python3.11-venv python3.11-dev

# Install Poetry
curl -sSL https://install.python-poetry.org | python3 -

# Add to PATH (add to ~/.bashrc for persistence)
export PATH="$HOME/.local/bin:$PATH"

# Verify
python3.11 --version
poetry --version

# Configure Poetry to create virtualenvs inside the project
poetry config virtualenvs.in-project true
```

---

## Step 2 — Install Node.js 20+

```bash
# Ubuntu / WSL (via NodeSource)
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt install -y nodejs

# Verify
node --version   # v20.x.x
npm --version    # 10.x.x
```

---

## Step 3 — Clone and install dependencies

```bash
cd repos/ai-multi-agent

# Install backend dependencies
poetry install

# Install frontend dependencies
cd frontend
npm install
cd ..
```

---

## Step 4 — Configure environment variables

```bash
cp .env.example .env
```

Edit `.env` with these key settings:

| Variable | Default | Description |
| --- | --- | --- |
| `CLOUD_PROVIDER` | `local` | LLM provider: `aws`, `azure`, `local` |
| `APP_PORT` | `8400` | Backend API port |
| `WS_PORT` | `8401` | WebSocket port |
| `FRONTEND_PORT` | `3000` | Frontend dev server port |
| `REDIS_URL` | _(empty)_ | Redis URL (leave empty for in-memory) |
| `DATABASE_URL` | _(empty)_ | Database URL (leave empty for SQLite) |
| `OLLAMA_BASE_URL` | `http://localhost:11434` | Ollama endpoint |
| `OLLAMA_MODEL` | `llama3.2` | Default Ollama model |

**Local provider settings (default — works out of the box):**

```bash
CLOUD_PROVIDER=local
# Ollama is auto-detected at http://localhost:11434
```

**AWS provider settings:**

```bash
CLOUD_PROVIDER=aws
AWS_REGION=eu-west-1
AWS_BEDROCK_MODEL=anthropic.claude-3-5-sonnet-20241022-v2:0
```

**Azure provider settings:**

```bash
CLOUD_PROVIDER=azure
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_API_KEY=your-key-here
AZURE_OPENAI_DEPLOYMENT=gpt-4o
AZURE_OPENAI_API_VERSION=2024-02-01
```

---

## Step 5 — Start the platform (local)

### Install Ollama and pull models

```bash
# Install Ollama
curl -fsSL https://ollama.com/install.sh | sh

# Pull required model
ollama pull llama3.2    # LLM (~2 GB)

# Verify
ollama list
```

### Start the backend

```bash
poetry run start
# → http://localhost:8400
# → Swagger UI at http://localhost:8400/docs
# → WebSocket at ws://localhost:8400/ws
```

### Start the frontend (in another terminal)

```bash
cd frontend
npm run dev
# → http://localhost:3000
```

### Verify both are running

```bash
curl http://localhost:8400/health | jq    # Backend
curl http://localhost:3000                  # Frontend (HTML response)
```

---

## Step 6 — Submit your first task

### Via API

```bash
curl -X POST http://localhost:8400/v1/tasks \
  -H "Content-Type: application/json" \
  -d '{
    "topic": "Compare AWS and Azure for enterprise AI deployments",
    "crew_mode": "sequential",
    "agents": ["researcher", "analyst", "writer", "critic"]
  }' | jq
```

### Via frontend

1. Open <http://localhost:3000>
2. Type a topic in the input box
3. Select crew mode (sequential or hierarchical)
4. Click "Run Crew"
5. Watch agents collaborate in real-time

### Check task status

```bash
# List all tasks
curl http://localhost:8400/v1/tasks | jq

# Get a specific task result
curl http://localhost:8400/v1/tasks/<task-id> | jq
```

### List available agents

```bash
curl http://localhost:8400/v1/agents | jq
```

---

## Step 7 — WebSocket testing

```bash
# Install wscat
npm install -g wscat

# Connect to global events
wscat -c ws://localhost:8400/ws

# In another terminal, submit a task
curl -X POST http://localhost:8400/v1/tasks \
  -d '{"topic": "Latest AI trends"}' \
  -H "Content-Type: application/json"

# Watch events stream in wscat terminal
```

You should see events like:

```json
{"event": "task_started", "task_id": "abc-123", "agents": ["researcher"]}
{"event": "agent_thinking", "agent": "researcher", "step": 1}
{"event": "agent_output", "agent": "researcher", "content": "..."}
{"event": "task_completed", "task_id": "abc-123"}
```

---

## Step 8 — Docker (full stack)

Run the entire platform (backend + frontend + Redis) with one command:

```bash
docker compose up -d

# Backend: http://localhost:8400
# Frontend: http://localhost:3000

# Watch logs
docker compose logs -f backend

# Cleanup
docker compose down -v
```

---

## Step 9 — Run Labs Locally

Once the platform is running (see [Step 5](#step-5--start-the-platform-local)), you can run all 8 hands-on labs.

**Cost: $0. No API keys needed. Runs entirely on your machine.**

### 9a. Automated (recommended)

```bash
# 1. Start the backend (in one terminal)
poetry run start

# 2. Run all labs (in another terminal)
poetry run python scripts/run_all_labs.py --env local
```

This runs all 8 hands-on labs against Ollama and prints a pass/fail report.

No infrastructure to deploy or destroy — it's all local.

**Results are saved to:** `scripts/lab_results/local/`

### 9b. Or run manually (step by step)

```bash
# Start the backend
poetry run start

# Then test manually via frontend at http://localhost:3000
# or Swagger UI at http://localhost:8400/docs
```

**Results location:** `scripts/lab_results/local/`

> **Note:** `run_cloud_labs.sh` is for cloud deployments only (AWS/Azure). It wraps
> `terraform apply` → labs → `terraform destroy`. For local development, use
> `run_all_labs.py` directly as shown above.

### Hardware requirements

| Component | Minimum | Recommended |
| --- | --- | --- |
| **RAM** | 8 GB | 16 GB |
| **Disk** | 5 GB (for models) | 10 GB |
| **GPU** | Not required (CPU works) | NVIDIA GPU (faster inference) |

---

## Step 10 — Connect to AWS (and run on AWS)

### 10a. Install AWS CLI

```bash
# Ubuntu / WSL
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip
sudo ./aws/install
aws --version
```

### 10b. Configure AWS credentials

**Option A: Access keys (simplest for personal account)**

```bash
aws configure
# AWS Access Key ID: <paste your key>
# AWS Secret Access Key: <paste your secret>
# Default region name: eu-west-1
# Default output format: json
```

Get your access keys from: AWS Console → IAM → Users → Your User → Security credentials → Create access key.

**Option B: SSO (if your account uses AWS Organizations)**

```bash
aws configure sso --profile ai-multi-agent
# Follow the prompts for SSO start URL, region, account, role
```

### 10c. Enable Bedrock model access

Bedrock models are not enabled by default. You need to request access:

1. Go to AWS Console → Amazon Bedrock → Model access
2. Click "Manage model access"
3. Enable:
   - **Anthropic → Claude 3.5 Sonnet v2** (for LLM)
4. Wait for approval (usually instant for personal accounts)

### 10d. Verify AWS connectivity

```bash
aws sts get-caller-identity
# Should show your account ID and ARN

aws bedrock list-foundation-models --region eu-west-1 \
  --query "modelSummaries[?contains(modelId, 'claude')].[modelId]" --output table
```

### Cost-saving tips for AWS

- **Bedrock**: Pay-per-token only. No idle costs. A typical development session costs < $1.
- **ElastiCache**: Charged by the hour. Use the smallest instance type for labs.
- **⚠️ Always destroy after labs** — the budget guard (€5 default) is your safety net.

### 10e. Deploy and run labs (automated)

```bash
./scripts/run_cloud_labs.sh --provider aws --email you@example.com
```

The script automatically:

1. `terraform apply` — deploys ECS, ElastiCache, and a budget guard
2. Starts the backend with `CLOUD_PROVIDER=aws`
3. Runs all 8 hands-on labs against AWS
4. Prints a pass/fail completion report
5. `terraform destroy` — tears down ALL infrastructure (even on Ctrl+C or errors)

**Budget control:** The default budget limit is €5. To increase it:

```bash
./scripts/run_cloud_labs.sh --provider aws --email you@example.com --cost-limit 15
```

**Results are saved to:** `scripts/lab_results/aws/`

### 10f. Or deploy and run manually (step by step)

```bash
# 1. Deploy infrastructure
cd infra/aws
terraform init
terraform apply -var="cost_limit_eur=5" -var="alert_email=you@example.com"

# 2. Set CLOUD_PROVIDER=aws in .env (see Step 4)

# 3. Start the backend
cd ../..  # back to repo root
poetry run start

# 4. Run labs automatically (in another terminal)
poetry run python scripts/run_all_labs.py --env aws

# OR — test manually via frontend at http://localhost:3000
# or Swagger UI at http://localhost:8400/docs

# 5. ALWAYS destroy when done
cd infra/aws
terraform destroy -var="cost_limit_eur=5" -var="alert_email=you@example.com"
```

> ⚠️ **CAUTION — Manual mode means manual cleanup!** When running manually, there
> is no automatic `terraform destroy` on exit. Monitor your costs in the
> [AWS Billing Console](https://console.aws.amazon.com/billing/)
> and **always run `terraform destroy` when finished.**

**Results location:** `scripts/lab_results/aws/`

---

## Step 11 — Connect to Azure (and run on Azure)

### 11a. Install Azure CLI

```bash
# Ubuntu / WSL
curl -sL https://aka.ms/InstallAzureCLIDeb | sudo bash
az --version
```

### 11b. Login to Azure

```bash
az login
# Opens a browser — sign in with your Azure account

# Set the active subscription (if you have multiple)
az account set --subscription "your-subscription-id"
```

### 11c. Create Azure OpenAI resource

1. Go to Azure Portal → Create a resource → "Azure OpenAI"
2. Select your subscription and resource group
3. Region: **West Europe** (cheapest in EU)
4. Pricing tier: **Standard S0**
5. After creation, go to the resource → Keys and Endpoint
6. Copy the **Endpoint** and **Key 1** to your `.env` file

### 11d. Deploy models in Azure OpenAI

1. Go to Azure AI Studio (<https://ai.azure.com>)
2. Select your Azure OpenAI resource
3. Go to Deployments → Create deployment
4. Deploy:
   - **gpt-4o** — deployment name: `gpt-4o`

### 11e. Verify Azure connectivity

```bash
az account show
# Should show your subscription

curl -X POST "https://your-resource.openai.azure.com/openai/deployments/gpt-4o/chat/completions?api-version=2024-02-01" \
  -H "api-key: your-key" \
  -H "Content-Type: application/json" \
  -d '{"messages": [{"role": "user", "content": "Hello"}], "max_tokens": 10}'
```

### Cost-saving tips for Azure

- **Azure OpenAI**: Pay-per-token. Development costs < $1/day.
- **⚠️ Always destroy after labs** — the budget guard (€5 default) is your safety net.

### 11f. Deploy and run labs (automated)

```bash
./scripts/run_cloud_labs.sh --provider azure --email you@example.com
```

The script automatically:

1. `terraform apply` — deploys Container Apps, Redis Cache, and a budget guard
2. Starts the backend with `CLOUD_PROVIDER=azure`
3. Runs all 8 hands-on labs against Azure
4. Prints a pass/fail completion report
5. `terraform destroy` — tears down ALL infrastructure (even on Ctrl+C or errors)

**Budget control:**

```bash
./scripts/run_cloud_labs.sh --provider azure --email you@example.com --cost-limit 15
```

**Results are saved to:** `scripts/lab_results/azure/`

### 11g. Or deploy and run manually (step by step)

```bash
# 1. Deploy infrastructure
cd infra/azure
terraform init
terraform apply -var="cost_limit_eur=5" -var="alert_email=you@example.com"

# 2. Set CLOUD_PROVIDER=azure in .env (see Step 4)

# 3. Start the backend
cd ../..  # back to repo root
poetry run start

# 4. Run labs automatically (in another terminal)
poetry run python scripts/run_all_labs.py --env azure

# OR — test manually via frontend at http://localhost:3000
# or Swagger UI at http://localhost:8400/docs

# 5. ALWAYS destroy when done
cd infra/azure
terraform destroy -var="cost_limit_eur=5" -var="alert_email=you@example.com"
```

> ⚠️ **CAUTION — Manual mode means manual cleanup!** When running manually, there
> is no automatic `terraform destroy` on exit. Monitor your costs in the
> [Azure Cost Management](https://portal.azure.com/#view/Microsoft_Azure_CostManagement)
> and **always run `terraform destroy` when finished.**

**Results location:** `scripts/lab_results/azure/`

---

## Step 12 — Run the Tests

```bash
# Backend tests
poetry run pytest tests/ -v

# With coverage
poetry run pytest tests/ -v --cov=src --cov-report=term-missing

# Frontend tests
cd frontend
npm run test
```

---

## Step 13 — Project Structure

```text
ai-multi-agent/
├── src/
│   ├── main.py              ← FastAPI app factory + lifespan
│   ├── config.py            ← Pydantic Settings
│   ├── models.py            ← Request/response models
│   ├── llm/
│   │   └── provider.py      ← LLM provider (Bedrock/Azure/Ollama)
│   ├── agents/
│   │   ├── researcher.py    ← Research agent
│   │   ├── analyst.py       ← Analysis agent
│   │   ├── writer.py        ← Writing agent
│   │   └── critic.py        ← Review/critique agent
│   ├── crew/
│   │   ├── orchestrator.py  ← Crew orchestration (sequential/hierarchical)
│   │   └── task_manager.py  ← Task lifecycle management
│   ├── websocket/
│   │   └── handler.py       ← WebSocket event streaming
│   └── routes/
│       ├── tasks.py          ← POST /v1/tasks, GET /v1/tasks
│       ├── agents.py         ← GET /v1/agents
│       └── health.py         ← GET /health
├── frontend/
│   ├── src/
│   │   ├── App.tsx           ← Main React app
│   │   ├── components/       ← UI components
│   │   └── hooks/            ← WebSocket + API hooks
│   ├── package.json
│   └── tsconfig.json
├── scripts/
│   ├── run_all_labs.py       ← 8 automated lab experiments
│   ├── run_cloud_labs.sh     ← One-command cloud deploy → run → destroy
│   └── lab_results/          ← Lab output (local/, aws/, azure/)
├── tests/
├── docs/
├── infra/
│   ├── aws/main.tf
│   └── azure/main.tf
├── docker-compose.yml
├── Dockerfile
└── pyproject.toml
```

---

## Troubleshooting

### Ollama not running

```bash
curl http://localhost:11434/api/tags
# If not running:
ollama serve
```

### Backend port already in use

```bash
lsof -i :8400
kill -9 <PID>
poetry run start
```

### Frontend port already in use

```bash
lsof -i :3000
kill -9 <PID>
cd frontend && npm run dev
```

### WebSocket connection refused

Make sure the backend is running first. The WebSocket server starts on the same port as the API (`ws://localhost:8400/ws`).

### ModuleNotFoundError (Python)

```bash
poetry install
```

### Frontend build errors

```bash
cd frontend
rm -rf node_modules
npm install
npm run dev
```

### Terraform errors

```bash
cd infra/aws   # or infra/azure
terraform init -upgrade
terraform plan -var="cost_limit_eur=5" -var="alert_email=you@example.com"
```
