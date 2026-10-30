from __future__ import annotations

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.core.ws_manager import ws_manager

router = APIRouter(tags=["WebSocket"])


@router.websocket("/ws/traces")
async def websocket_traces(websocket: WebSocket):
    """
    WebSocket endpoint for real-time trace streaming and live evaluation feedback.
    Clients receive TRACE_INGESTED and REPORT_READY events.
    """
    await ws_manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()  # Keeps connection open
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)
