"""Tests for WebSocket manager."""

from unittest.mock import AsyncMock

import pytest

from src.models import AgentEvent, AgentRole, EventType
from src.websocket.manager import WebSocketManager


@pytest.fixture
def manager():
    return WebSocketManager()


def make_mock_ws():
    ws = AsyncMock()
    ws.accept = AsyncMock()
    ws.send_text = AsyncMock()
    return ws


async def test_connect_global(manager):
    ws = make_mock_ws()
    await manager.connect(ws)
    assert manager.connection_count == 1


async def test_connect_task_specific(manager):
    ws = make_mock_ws()
    await manager.connect(ws, task_id="task-1")
    assert manager.connection_count == 1
    assert "task-1" in manager.connections


async def test_disconnect(manager):
    ws = make_mock_ws()
    await manager.connect(ws)
    assert manager.connection_count == 1
    manager.disconnect(ws)
    assert manager.connection_count == 0


async def test_broadcast_to_task(manager):
    ws = make_mock_ws()
    await manager.connect(ws, task_id="task-1")

    event = AgentEvent(
        type=EventType.AGENT_THINKING,
        task_id="task-1",
        agent=AgentRole.RESEARCHER,
        content="Thinking...",
    )

    await manager.broadcast(event)
    ws.send_text.assert_called_once()


async def test_broadcast_to_global(manager):
    ws = make_mock_ws()
    await manager.connect(ws)

    event = AgentEvent(
        type=EventType.TASK_STARTED,
        task_id="task-1",
        content="Started",
    )

    await manager.broadcast(event)
    ws.send_text.assert_called_once()


async def test_broadcast_removes_disconnected(manager):
    ws = make_mock_ws()
    ws.send_text.side_effect = Exception("disconnected")
    await manager.connect(ws)

    event = AgentEvent(
        type=EventType.TASK_STARTED,
        task_id="task-1",
        content="Started",
    )

    await manager.broadcast(event)
    assert manager.connection_count == 0
