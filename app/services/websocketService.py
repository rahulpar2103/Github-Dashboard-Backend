import asyncio
from fastapi import WebSocket, WebSocketDisconnect
from app.services.githubService import github_service
from app.services.repoStoreService import repo_store_service

class WebSocketService:
    async def websocket(self, ws: WebSocket, repo_name: str):
        await ws.accept()
        await repo_store_service.add_tracked_repo(repo_name)
        try:
            while True:
                filtered_data = await github_service.get_new_repo_events(repo_name)
                if filtered_data:
                    await ws.send_json(filtered_data)
                await asyncio.sleep(10)
        except WebSocketDisconnect:
            print("Client disconnected!")

websocket_service = WebSocketService()

