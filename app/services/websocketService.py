import asyncio
import json
from fastapi import WebSocket, WebSocketDisconnect
from app.services.githubService import github_service
from app.services.repoStoreService import repo_store_service
from app.core.redis import redis_client

class WebSocketService:
    async def websocket(self, ws: WebSocket, repo_name: str, user_id: str = "0"):
        await ws.accept()
        await repo_store_service.add_tracked_repo(user_id, repo_name)
        initial_events = await repo_store_service.get_events(repo_name)
        if initial_events is None:
            initial_events = await github_service.track_repository(repo_name, user_id=user_id)
        if initial_events:
            await ws.send_json(initial_events)
        pubsub = redis_client.pubsub()
        channel = f"channel:events:{repo_name}"
        await pubsub.subscribe(channel)
        try:
            while True:
                message = await pubsub.get_message(ignore_subscribe_messages=True, timeout=1.0)
                if message and message["type"] == "message":
                    data = json.loads(message["data"])
                    await ws.send_json(data)
                await asyncio.sleep(0.1)
        except WebSocketDisconnect:
            print(f"Client disconnected from {repo_name}!")
        finally:
            await pubsub.unsubscribe(channel)
            await pubsub.close()

websocket_service = WebSocketService()
