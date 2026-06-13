import asyncio
from fastapi import WebSocket, WebSocketDisconnect
from app.services.githubService import github_service
from app.services.repoStoreService import repo_store_service

class WebSocketService:
    async def websocket(self, ws: WebSocket, repo_name: str):
        await ws.accept()
        try:
            max_id = await repo_store_service.get_max_id(repo_name)
            
            while True:
                data = await github_service.get_repo_events(repo_name)
                filtered_data = [event for event in data if int(event["id"])>max_id]
                if filtered_data:
                    max_id=max([int(event["id"]) for event in filtered_data])
                    await repo_store_service.set_max_id(repo_name, max_id)
                    await ws.send_json(filtered_data)
                await asyncio.sleep(10)
        except WebSocketDisconnect:
            print("Client disconnected")
 
websocket_service = WebSocketService()