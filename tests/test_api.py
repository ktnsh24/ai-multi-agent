"""Tests for API routes."""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from fastapi.testclient import TestClient

from src.main import create_app
from src.models import AgentRole, CrewMode, TaskStatus
from src.tasks.store import InMemoryTaskStore
from src.websocket.manager import WebSocketManager


@pytest.fixture
def client():
    app = create_app()

    # Override lifespan components
    app.state.settings = MagicMock()
    app.state.settings.cloud_provider = MagicMock()
    app.state.settings.cloud_provider.value = "local"
    app.state.settings.ollama_model = "llama3.2"
    app.state.llm_provider = MagicMock()
    app.state.crew_orchestrator = MagicMock()
    app.state.task_store = InMemoryTaskStore()
    app.state.ws_manager = WebSocketManager()

    with TestClient(app, raise_server_exceptions=False) as client:
        yield client


def test_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["version"] == "0.1.0"


def test_submit_task(client):
    response = client.post(
        "/v1/tasks",
        json={
            "topic": "AI trends",
            "crew_mode": "sequential",
            "agents": ["researcher", "analyst", "writer", "critic"],
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["task_id"]
    assert data["status"] == "pending"
    assert data["topic"] == "AI trends"


def test_list_tasks(client):
    # Submit a task first
    client.post("/v1/tasks", json={"topic": "Test task"})
    response = client.get("/v1/tasks")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1


def test_get_task(client):
    # Submit a task
    submit_response = client.post("/v1/tasks", json={"topic": "Test task"})
    task_id = submit_response.json()["task_id"]

    response = client.get(f"/v1/tasks/{task_id}")
    assert response.status_code == 200
    assert response.json()["task_id"] == task_id


def test_get_nonexistent_task(client):
    response = client.get("/v1/tasks/nonexistent")
    assert response.status_code == 404


def test_delete_task(client):
    submit_response = client.post("/v1/tasks", json={"topic": "Test task"})
    task_id = submit_response.json()["task_id"]

    response = client.delete(f"/v1/tasks/{task_id}")
    assert response.status_code == 200
    assert response.json()["deleted"] is True


def test_delete_nonexistent_task(client):
    response = client.delete("/v1/tasks/nonexistent")
    assert response.status_code == 404


def test_submit_with_context(client):
    response = client.post(
        "/v1/tasks",
        json={
            "topic": "Cloud migration",
            "context": "Focus on AWS services",
            "crew_mode": "hierarchical",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["crew_mode"] == "hierarchical"
