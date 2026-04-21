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
