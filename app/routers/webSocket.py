from fastapi import APIRouter, WebSocket
from app.services.websocketService import websocket_service

router = APIRouter()

@router.websocket("/ws")
async def websocket_endpoint(ws: WebSocket, repo_name: str, user_id: str = "0"):
    await websocket_service.websocket(ws, repo_name, user_id=user_id)