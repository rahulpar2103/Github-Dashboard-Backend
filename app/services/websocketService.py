import asyncio
from fastapi import WebSocket, WebSocketDisconnect
from app.services.githubService import github_service

class WebSocketService:
    async def websocket(self, ws: WebSocket):
        await ws.accept()
        try:
            max_id=0
            while True:
                data=await github_service.get_repo_events("rahulpar2103/Github-Dashboard-Backend")
                filtered_data = [event for event in data if int(event["id"])>max_id]
                if filtered_data:
                    max_id=max([int(event["id"]) for event in filtered_data])
                    await ws.send_json(filtered_data)
                await asyncio.sleep(10)
        except WebSocketDisconnect:
            print("Client disconnected")

websocket_service = WebSocketService()