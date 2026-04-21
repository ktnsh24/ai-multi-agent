"""
AI Multi-Agent — Integration Tests

Tests the full request pipeline: route → task store → crew orchestrator → WebSocket.
Components are mocked at app.state level; task store and WebSocket manager are real.

Test inventory (20 tests):
    TestTaskSubmission          — Submit tasks, validate response format (4 tests)
    TestTaskCRUD                — Create, read, list, delete tasks (5 tests)
    TestTaskConfiguration       — Custom crew modes, agents, context (4 tests)
    TestTaskErrorHandling       — Not found, validation errors (3 tests)
    TestHealthEndpoint          — Health check with components (2 tests)
    TestWebSocketManager        — Connection management, broadcasting (2 tests)
"""

import pytest
from unittest.mock import AsyncMock

from src.models import AgentEvent, AgentRole, CrewMode, EventType
from src.websocket.manager import WebSocketManager


# ---------------------------------------------------------------------------
# Task Submission
# ---------------------------------------------------------------------------
class TestTaskSubmission:
    """Integration: task submission and response format."""

    def test_submit_returns_200(self, client):
        response = client.post("/v1/tasks", json={"topic": "AI trends"})
        assert response.status_code == 200

    def test_submit_returns_task_response(self, client):
        response = client.post("/v1/tasks", json={"topic": "AI trends"})
        data = response.json()
        assert "task_id" in data
        assert data["status"] == "pending"
        assert data["topic"] == "AI trends"

    def test_submit_returns_crew_mode(self, client):
        response = client.post("/v1/tasks", json={"topic": "Test"})
        data = response.json()
        assert data["crew_mode"] == "sequential"
        assert "agents" in data

    def test_submit_returns_created_at(self, client):
        response = client.post("/v1/tasks", json={"topic": "Test"})
        data = response.json()
        assert "created_at" in data


# ---------------------------------------------------------------------------
# Task CRUD
# ---------------------------------------------------------------------------
class TestTaskCRUD:
    """Integration: full task lifecycle."""

    def test_create_and_get(self, client):
        r = client.post("/v1/tasks", json={"topic": "Test"})
        task_id = r.json()["task_id"]
        detail = client.get(f"/v1/tasks/{task_id}")
        assert detail.status_code == 200
        assert detail.json()["task_id"] == task_id

    def test_list_tasks(self, client):
        client.post("/v1/tasks", json={"topic": "Task 1"})
        client.post("/v1/tasks", json={"topic": "Task 2"})
        response = client.get("/v1/tasks")
        assert response.status_code == 200
        assert len(response.json()) >= 2

    def test_list_empty(self, client):
        response = client.get("/v1/tasks")
        assert response.status_code == 200
        assert response.json() == []

    def test_delete_task(self, client):
        r = client.post("/v1/tasks", json={"topic": "Delete me"})
        task_id = r.json()["task_id"]
        response = client.delete(f"/v1/tasks/{task_id}")
        assert response.status_code == 200
        assert response.json()["deleted"] is True

    def test_deleted_task_gone(self, client):
        r = client.post("/v1/tasks", json={"topic": "Delete me"})
        task_id = r.json()["task_id"]
        client.delete(f"/v1/tasks/{task_id}")
        response = client.get(f"/v1/tasks/{task_id}")
        assert response.status_code == 404


# ---------------------------------------------------------------------------
# Task Configuration
# ---------------------------------------------------------------------------
class TestTaskConfiguration:
    """Integration: custom task configuration."""

    def test_hierarchical_mode(self, client):
        response = client.post(
            "/v1/tasks",
            json={"topic": "Test", "crew_mode": "hierarchical"},
        )
        assert response.json()["crew_mode"] == "hierarchical"

    def test_custom_agents(self, client):
        response = client.post(
            "/v1/tasks",
            json={"topic": "Test", "agents": ["researcher", "writer"]},
        )
        agents = response.json()["agents"]
        assert len(agents) == 2
        assert "researcher" in agents

    def test_with_context(self, client):
        response = client.post(
            "/v1/tasks",
            json={"topic": "Cloud migration", "context": "Focus on AWS"},
        )
        assert response.status_code == 200

    def test_default_agents(self, client):
        response = client.post("/v1/tasks", json={"topic": "Test"})
        agents = response.json()["agents"]
        assert len(agents) == 4
        assert "researcher" in agents
        assert "critic" in agents


# ---------------------------------------------------------------------------
# Error Handling
# ---------------------------------------------------------------------------
class TestTaskErrorHandling:
    """Integration: error paths."""

    def test_get_nonexistent_returns_404(self, client):
        response = client.get("/v1/tasks/does-not-exist")
        assert response.status_code == 404

    def test_delete_nonexistent_returns_404(self, client):
        response = client.delete("/v1/tasks/does-not-exist")
        assert response.status_code == 404

    def test_missing_topic_returns_422(self, client):
        response = client.post("/v1/tasks", json={})
        assert response.status_code == 422


# ---------------------------------------------------------------------------
# Health Endpoint
# ---------------------------------------------------------------------------
class TestHealthEndpoint:
    """Integration: health check."""

    def test_health_returns_200(self, client):
        response = client.get("/health")
        assert response.status_code == 200

    def test_health_shows_components(self, client):
        data = client.get("/health").json()
        assert data["status"] == "healthy"
        assert data["version"] == "0.1.0"
        assert "components" in data


# ---------------------------------------------------------------------------
# WebSocket Manager
# ---------------------------------------------------------------------------
class TestWebSocketManagerIntegration:
    """Integration: WebSocket manager with events."""

    @pytest.mark.asyncio
    async def test_broadcast_to_connected_client(self, ws_manager):
        ws = AsyncMock()
        ws.accept = AsyncMock()
        ws.send_text = AsyncMock()
        await ws_manager.connect(ws, task_id="task-1")

        event = AgentEvent(
            type=EventType.AGENT_THINKING,
            task_id="task-1",
            agent=AgentRole.RESEARCHER,
            content="Thinking...",
        )
        await ws_manager.broadcast(event)
        ws.send_text.assert_called_once()

    @pytest.mark.asyncio
    async def test_disconnect_removes_client(self, ws_manager):
        ws = AsyncMock()
        ws.accept = AsyncMock()
        await ws_manager.connect(ws)
        assert ws_manager.connection_count == 1
        ws_manager.disconnect(ws)
        assert ws_manager.connection_count == 0
