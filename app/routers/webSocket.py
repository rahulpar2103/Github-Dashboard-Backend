from fastapi import APIRouter, WebSocket
from app.services.websocketService import websocket_service

router = APIRouter()

@router.websocket("/ws")
async def websocket_endpoint(ws: WebSocket, repo_name: str):
    await websocket_service.websocket(ws, repo_name)