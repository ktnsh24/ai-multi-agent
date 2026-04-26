"""WebSocket manager for real-time agent events."""

import logging

from fastapi import WebSocket

from src.models import AgentEvent

logger = logging.getLogger(__name__)


class WebSocketManager:
    """Manages WebSocket connections and broadcasts agent events."""

    def __init__(self) -> None:
        # task_id → set of connected websockets
        self.connections: dict[str, set[WebSocket]] = {}
        # Global broadcast connections (all events)
        self.global_connections: set[WebSocket] = set()

    async def connect(self, websocket: WebSocket, task_id: str | None = None) -> None:
        """Accept a new WebSocket connection."""
        await websocket.accept()

        if task_id:
            if task_id not in self.connections:
                self.connections[task_id] = set()
            self.connections[task_id].add(websocket)
            logger.info("WebSocket connected for task %s", task_id)
        else:
            self.global_connections.add(websocket)
            logger.info("WebSocket connected (global)")

    def disconnect(self, websocket: WebSocket, task_id: str | None = None) -> None:
        """Remove a disconnected WebSocket."""
        if task_id and task_id in self.connections:
            self.connections[task_id].discard(websocket)
            if not self.connections[task_id]:
                del self.connections[task_id]
        self.global_connections.discard(websocket)

    async def broadcast(self, event: AgentEvent) -> None:
        """Broadcast an event to all connected clients for a task."""
        data = event.model_dump_json()

        # Send to task-specific connections
        if event.task_id in self.connections:
            disconnected = set()
            for ws in self.connections[event.task_id]:
                try:
                    await ws.send_text(data)
                except Exception:
                    disconnected.add(ws)

            for ws in disconnected:
                self.connections[event.task_id].discard(ws)

        # Send to global connections
        disconnected = set()
        for ws in self.global_connections:
            try:
                await ws.send_text(data)
            except Exception:
                disconnected.add(ws)

        for ws in disconnected:
            self.global_connections.discard(ws)

    @property
    def connection_count(self) -> int:
        """Total number of active connections."""
        task_count = sum(len(conns) for conns in self.connections.values())
        return task_count + len(self.global_connections)
