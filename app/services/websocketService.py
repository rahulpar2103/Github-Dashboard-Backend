import asyncio
import json
from fastapi import WebSocket, WebSocketDisconnect
from app.services.githubService import github_service
from app.services.repoStoreService import repo_store_service
from app.core.redis import redis_client

class WebSocketService:
    async def websocket(self, ws: WebSocket, repo_name: str, user_id: str = "0"):
        await ws.accept()
        
        # 1. Add repository to tracked repositories to start background polling for this user
        await repo_store_service.add_tracked_repo(user_id, repo_name)
        
        # 2. Retrieve and send initial cached events immediately so the UI is populated
        initial_events = await repo_store_service.get_events(repo_name)
        if initial_events is None:
            # Fall back to track/fetch directly if not cached yet
            initial_events = await github_service.track_repository(repo_name, user_id=user_id)
        
        if initial_events:
            await ws.send_json(initial_events)
            
        # 3. Create a Pub/Sub client and subscribe to the repository's event channel
        pubsub = redis_client.pubsub()
        channel = f"channel:events:{repo_name}"
        await pubsub.subscribe(channel)
        
        try:
            while True:
                # get_message yields control and waits up to 1 second
                message = await pubsub.get_message(ignore_subscribe_messages=True, timeout=1.0)
                if message and message["type"] == "message":
                    data = json.loads(message["data"])
                    await ws.send_json(data)
                
                # Small sleep to prevent any tight loop CPU overhead
                await asyncio.sleep(0.1)
        except WebSocketDisconnect:
            print(f"Client disconnected from {repo_name}!")
        finally:
            # Clean up the Pub/Sub subscription and connection when the client disconnects
            await pubsub.unsubscribe(channel)
            await pubsub.close()

websocket_service = WebSocketService()
