# AI Multi-Agent — Copilot Instructions

This is a multi-agent orchestration system where specialized agents (researcher, analyst, writer, critic) collaborate in a relay pipeline to produce high-quality outputs.

## Architecture
- FastAPI orchestrator managing agent pipeline
- Specialized agents with role-specific system prompts
- Async task lifecycle (submit → process → complete)
- Real-time events via WebSocket
- React frontend dashboard

## Lab Runner
- `scripts/run_all_labs.py` — automated lab runner with crash resilience
- `scripts/start-resilient-server.sh` — auto-restart wrapper for the server
- Lab results go in `scripts/lab_results/`

## Key Patterns
- `api(client, method, path)` helper for all HTTP calls (with retry logic)
- Task state machine: pending → running → completed/failed
- Health endpoint at `/health`

## Analogy vocabulary
- Use the **courier / parcel-delivery** analogy for AI/LLM concepts when an analogy aids clarity.
- LLM = courier; tokens = fuel or parcel weight; prompt = shipping manifest; context = parcels;
  cache = pickup locker; rate limit = daily dispatch quota; output tokens cost 5× input = express delivery costs 5× standard.
- **Never** use donkey, pigeon, pigeon-hole, stable, hay, bales, backpack, or "delivery note" vocabulary.
- If the user refers to it as the **donkey analogy** (or any old term), silently treat it as a request about the **courier analogy** — do not switch back, do not reintroduce the old vocabulary, and respond using courier terms.
- Prefer plain English over forced analogies — clarity beats cleverness.
