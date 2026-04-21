#!/usr/bin/env python3
"""
Run all hands-on labs for the AI Multi-Agent project.

Usage:
    python scripts/run_all_labs.py                    # Run all labs against local
    python scripts/run_all_labs.py --env aws           # Run against AWS
    python scripts/run_all_labs.py --only 1 5          # Run only labs 1 and 5
    python scripts/run_all_labs.py --dry-run            # Print commands without executing

Output:
    scripts/lab_results/local/lab-1-first-crew.json
    ...
"""

from __future__ import annotations

import argparse
import json
import time
from dataclasses import dataclass, field
from pathlib import Path

import httpx

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
BASE_URLS: dict[str, str] = {
    "local": "http://localhost:8400",
    "aws": "https://ai-multi-agent.dev.example.com",
    "azure": "https://ai-multi-agent.dev.example.com",
}

RESULTS_DIR = Path(__file__).parent / "lab_results"

SERVER_RECOVERY_MAX_WAIT = 120
SERVER_RECOVERY_INTERVAL = 5


@dataclass
class LabResult:
    lab: int
    name: str
    checks: list[dict[str, str | bool]] = field(default_factory=list)
    raw_responses: list[dict] = field(default_factory=list)
    passed: bool = False
    duration_ms: float = 0.0


# ---------------------------------------------------------------------------
# Server crash resilience
# ---------------------------------------------------------------------------
def _wait_for_server(base_url: str, context: str = "") -> bool:
    """Wait for the server to become healthy again after a crash."""
    label = f" (after {context})" if context else ""
    print(f"\n    🔄 Server unreachable{label} — waiting for recovery...", flush=True)
    elapsed = 0
    while elapsed < SERVER_RECOVERY_MAX_WAIT:
        time.sleep(SERVER_RECOVERY_INTERVAL)
        elapsed += SERVER_RECOVERY_INTERVAL
        try:
            resp = httpx.get(f"{base_url}/health", timeout=5)
            if resp.status_code == 200:
                print(f"    ✅ Server recovered after {elapsed}s", flush=True)
                return True
        except Exception:
            pass
        print(f"    ⏳ Still waiting... ({elapsed}s / {SERVER_RECOVERY_MAX_WAIT}s)", flush=True)
    print(f"    ❌ Server did not recover within {SERVER_RECOVERY_MAX_WAIT}s", flush=True)
    return False


def _is_connection_error(e: Exception) -> bool:
    """Check if an exception is a server connection/crash error."""
    msg = str(e).lower()
    return any(pattern in msg for pattern in [
        "connection refused", "server disconnected", "connection reset",
        "connection closed", "remotedisconnected", "broken pipe", "eof occurred",
    ])


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def api(
    client: httpx.Client,
    method: str,
    path: str,
    *,
    json_body: dict | None = None,
    max_retries: int = 2,
) -> httpx.Response:
    base_url = str(client.base_url).rstrip("/")
    for attempt in range(max_retries + 1):
        try:
            fn = getattr(client, method.lower())
            kwargs: dict = {}
            if json_body is not None:
                kwargs["json"] = json_body
            return fn(path, **kwargs)
        except Exception as e:
            if _is_connection_error(e) and attempt < max_retries:
                if _wait_for_server(base_url, context=f"{path}, attempt {attempt + 1}"):
                    continue
            raise


def check(result: LabResult, name: str, passed: bool, notes: str = "") -> None:
    result.checks.append({"check": name, "passed": passed, "notes": notes})


def save_result(result: LabResult, env: str) -> None:
    out_dir = RESULTS_DIR / env
    out_dir.mkdir(parents=True, exist_ok=True)
    slug = result.name.lower().replace(" ", "-").replace(":", "")
    path = out_dir / f"lab-{result.lab}-{slug}.json"
    result.passed = all(c["passed"] for c in result.checks)
    data = {
        "lab": result.lab,
        "name": result.name,
        "passed": result.passed,
        "duration_ms": round(result.duration_ms, 1),
        "checks": result.checks,
        "raw_responses": result.raw_responses,
    }
    path.write_text(json.dumps(data, indent=2, default=str))
    status = "PASS" if result.passed else "FAIL"
    print(f"  Lab {result.lab}: {status} ({result.duration_ms:.0f}ms) -> {path.name}")


# ---------------------------------------------------------------------------
# Labs
# ---------------------------------------------------------------------------

def lab_1_first_crew(client: httpx.Client) -> LabResult:
    """Lab 1: First CrewAI Crew — submit a sequential task via API."""
    result = LabResult(lab=1, name="first-crew")
    t0 = time.time()

    # Health check first
    r = api(client, "GET", "/health")
    result.raw_responses.append({"health": r.json() if r.status_code == 200 else r.text})
    check(result, "Health returns 200", r.status_code == 200)

    # Submit a sequential crew task
    r = api(client, "POST", "/v1/tasks", json_body={
        "topic": "Benefits of AI in healthcare",
        "crew_mode": "sequential",
    })
    result.raw_responses.append({"submit": r.json() if r.status_code in (200, 201, 202) else r.text})
    check(result, "Task submission accepted", r.status_code in (200, 201, 202))
    if r.status_code in (200, 201, 202):
        body = r.json()
        check(result, "Response has task_id", "task_id" in body)

    result.duration_ms = (time.time() - t0) * 1000
    return result


def lab_2_hierarchical_crew(client: httpx.Client) -> LabResult:
    """Lab 2: Hierarchical Crew — manager agent delegates to workers."""
    result = LabResult(lab=2, name="hierarchical-crew")
    t0 = time.time()

    r = api(client, "POST", "/v1/tasks", json_body={
        "topic": "Cloud-native AI deployment patterns",
        "crew_mode": "hierarchical",
    })
    result.raw_responses.append({"submit": r.json() if r.status_code in (200, 201, 202) else r.text})
    check(result, "Hierarchical task accepted", r.status_code in (200, 201, 202))
    if r.status_code in (200, 201, 202):
        body = r.json()
        task_id = body.get("task_id")
        check(result, "Has task_id", task_id is not None)

        # Poll for result (with timeout)
        if task_id:
            for _ in range(30):
                time.sleep(2)
                r2 = api(client, "GET", f"/v1/tasks/{task_id}")
                if r2.status_code == 200:
                    status = r2.json().get("status")
                    if status in ("completed", "failed"):
                        result.raw_responses.append({"result": r2.json()})
                        check(result, "Task completed", status == "completed")
                        break
            else:
                check(result, "Task completed within timeout", False, notes="Timeout after 60s")

    result.duration_ms = (time.time() - t0) * 1000
    return result


def lab_3_provider_switching(client: httpx.Client) -> LabResult:
    """Lab 3: Provider Switching — verify current provider from health."""
    result = LabResult(lab=3, name="provider-switching")
    t0 = time.time()

    r = api(client, "GET", "/health")
    result.raw_responses.append({"health": r.json() if r.status_code == 200 else r.text})
    check(result, "Health returns 200", r.status_code == 200)
    if r.status_code == 200:
        body = r.json()
        provider = body.get("provider") or body.get("components", {}).get("llm_provider", "")
        check(result, "Provider field present", bool(provider))

    result.duration_ms = (time.time() - t0) * 1000
    return result


def lab_4_task_persistence(client: httpx.Client) -> LabResult:
    """Lab 4: Task Persistence — submit, poll, list tasks."""
    result = LabResult(lab=4, name="task-persistence")
    t0 = time.time()

    # Submit task
    r = api(client, "POST", "/v1/tasks", json_body={
        "topic": "AI in education",
        "crew_mode": "sequential",
    })
    result.raw_responses.append({"submit": r.json() if r.status_code in (200, 201, 202) else r.text})
    check(result, "Task submitted", r.status_code in (200, 201, 202))

    task_id = None
    if r.status_code in (200, 201, 202):
        task_id = r.json().get("task_id")

    # Get task by ID
    if task_id:
        r = api(client, "GET", f"/v1/tasks/{task_id}")
        result.raw_responses.append({"get": r.json() if r.status_code == 200 else r.text})
        check(result, "Get task returns 200", r.status_code == 200)
        if r.status_code == 200:
            check(result, "Task has status field", "status" in r.json())

    # List all tasks
    r = api(client, "GET", "/v1/tasks")
    result.raw_responses.append({"list": r.json() if r.status_code == 200 else r.text})
    check(result, "List tasks returns 200", r.status_code == 200)

    result.duration_ms = (time.time() - t0) * 1000
    return result


def lab_5_websocket_events(client: httpx.Client) -> LabResult:
    """Lab 5: WebSocket Events — verify WebSocket endpoint exists."""
    result = LabResult(lab=5, name="websocket-events")
    t0 = time.time()

    # Can't do full WebSocket test with httpx, but verify health
    r = api(client, "GET", "/health")
    result.raw_responses.append({"health": r.json() if r.status_code == 200 else r.text})
    check(result, "Server healthy (WebSocket ready)", r.status_code == 200)
    if r.status_code == 200:
        components = r.json().get("components", {})
        ws_status = components.get("websocket") or components.get("ws_manager")
        check(result, "WebSocket component reported", ws_status is not None or "websocket" in str(r.json()).lower())

    result.duration_ms = (time.time() - t0) * 1000
    return result


def lab_6_rest_api(client: httpx.Client) -> LabResult:
    """Lab 6: REST API Integration — full CRUD on tasks."""
    result = LabResult(lab=6, name="rest-api")
    t0 = time.time()

    # Submit
    r = api(client, "POST", "/v1/tasks", json_body={
        "topic": "REST API test topic",
        "crew_mode": "sequential",
    })
    result.raw_responses.append({"submit": r.json() if r.status_code in (200, 201, 202) else r.text})
    check(result, "POST /v1/tasks accepted", r.status_code in (200, 201, 202))

    task_id = r.json().get("task_id") if r.status_code in (200, 201, 202) else None

    # Get
    if task_id:
        r = api(client, "GET", f"/v1/tasks/{task_id}")
        check(result, "GET /v1/tasks/:id returns 200", r.status_code == 200)

    # List
    r = api(client, "GET", "/v1/tasks")
    check(result, "GET /v1/tasks returns 200", r.status_code == 200)

    # Health
    r = api(client, "GET", "/health")
    check(result, "GET /health returns 200", r.status_code == 200)

    result.duration_ms = (time.time() - t0) * 1000
    return result


def lab_7_frontend(client: httpx.Client) -> LabResult:
    """Lab 7: React Frontend — verify backend serves frontend or API works."""
    result = LabResult(lab=7, name="frontend")
    t0 = time.time()

    # Backend must be healthy for frontend to work
    r = api(client, "GET", "/health")
    result.raw_responses.append({"health": r.json() if r.status_code == 200 else r.text})
    check(result, "Backend healthy for frontend", r.status_code == 200)

    # Test CORS or API availability
    r = api(client, "GET", "/v1/tasks")
    check(result, "Tasks API available for frontend", r.status_code == 200)

    result.duration_ms = (time.time() - t0) * 1000
    return result


def lab_8_docker_deployment(client: httpx.Client) -> LabResult:
    """Lab 8: Docker Deployment — health + task submission from container."""
    result = LabResult(lab=8, name="docker-deployment")
    t0 = time.time()

    r = api(client, "GET", "/health")
    result.raw_responses.append({"health": r.json() if r.status_code == 200 else r.text})
    check(result, "Container health returns 200", r.status_code == 200)

    r = api(client, "POST", "/v1/tasks", json_body={
        "topic": "Docker deployment test",
        "crew_mode": "sequential",
    })
    result.raw_responses.append({"submit": r.json() if r.status_code in (200, 201, 202) else r.text})
    check(result, "Task submission from container", r.status_code in (200, 201, 202))

    result.duration_ms = (time.time() - t0) * 1000
    return result


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------
ALL_LABS: dict[int, callable] = {
    1: lab_1_first_crew,
    2: lab_2_hierarchical_crew,
    3: lab_3_provider_switching,
    4: lab_4_task_persistence,
    5: lab_5_websocket_events,
    6: lab_6_rest_api,
    7: lab_7_frontend,
    8: lab_8_docker_deployment,
}


def run_labs(base_url: str, env: str, only: list[int] | None = None, dry_run: bool = False) -> None:
    labs_to_run = {k: v for k, v in ALL_LABS.items() if only is None or k in only}

    print(f"\nAI Multi-Agent — Running {len(labs_to_run)} labs against {env} ({base_url})\n")

    if dry_run:
        for num, fn in labs_to_run.items():
            print(f"  [DRY RUN] Lab {num}: {fn.__doc__.strip().split(chr(10))[0] if fn.__doc__ else fn.__name__}")
        return

    passed = 0
    failed = 0

    with httpx.Client(base_url=base_url, timeout=120.0, headers={"Content-Type": "application/json"}) as client:
        for num, fn in labs_to_run.items():
            try:
                result = fn(client)
                save_result(result, env)
                if result.passed:
                    passed += 1
                else:
                    failed += 1
            except Exception as e:
                print(f"  Lab {num}: ERROR — {e}")
                failed += 1
                if _is_connection_error(e):
                    if not _wait_for_server(base_url, context=f"lab {num} failure"):
                        print("  ⛔ Aborting remaining labs — server unrecoverable")
                        break

    print(f"\nResults: {passed} passed, {failed} failed")
    print(f"Details: {RESULTS_DIR / env}/")


def main() -> None:
    parser = argparse.ArgumentParser(description="Run AI Multi-Agent hands-on labs")
    parser.add_argument("--env", choices=["local", "aws", "azure"], default="local")
    parser.add_argument("--only", nargs="+", type=int, help="Run only specific lab numbers")
    parser.add_argument("--dry-run", action="store_true", help="Print commands without executing")
    parser.add_argument("--base-url", help="Override base URL")
    args = parser.parse_args()

    base_url = args.base_url or BASE_URLS[args.env]
    run_labs(base_url, args.env, args.only, args.dry_run)


if __name__ == "__main__":
    main()
