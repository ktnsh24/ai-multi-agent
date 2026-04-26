"""WebSocket route for real-time agent events."""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

router = APIRouter()


@router.websocket("/ws")
async def websocket_global(websocket: WebSocket) -> None:
    """Global WebSocket — receives all agent events."""

    ws_manager = websocket.app.state.ws_manager
    await ws_manager.connect(websocket)
    try:
        while True:
            # Keep connection alive; client can send pings
            _data = await websocket.receive_text()
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)


@router.websocket("/ws/{task_id}")
async def websocket_task(websocket: WebSocket, task_id: str) -> None:
    """Task-specific WebSocket — receives events for one task."""
    ws_manager = websocket.app.state.ws_manager
    await ws_manager.connect(websocket, task_id=task_id)
    try:
        while True:
            _data = await websocket.receive_text()
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket, task_id=task_id)
