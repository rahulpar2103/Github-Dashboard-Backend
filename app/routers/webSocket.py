from fastapi import APIRouter, WebSocket
import asyncio
router = APIRouter()

@router.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    await ws.accept()

    while True:
        await ws.send_text("hello")
        await asyncio.sleep(5)