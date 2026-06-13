import asyncio
from fastapi import WebSocket, WebSocketDisconnect

class WebSocketService:
    async def websocket(self, ws: WebSocket):
        await ws.accept()
        try:
            while True:
                await ws.send_text("hello")
                await asyncio.sleep(2)
        except WebSocketDisconnect:
            pass

websocket_service = WebSocketService()