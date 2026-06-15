from app.core.redis import redis_client as global_redis_client
import json

class RepoStoreService:
    async def get_max_id(self, repo_name: str, redis_client=None) -> int:
        client = redis_client or global_redis_client
        key = f"github:{repo_name}:max_id"
        max_id = await client.get(key)
        if max_id:
            return int(max_id)
        return 0

    async def set_max_id(self, repo_name: str, max_id: int, redis_client=None):
        client = redis_client or global_redis_client
        key = f"github:{repo_name}:max_id"
        await client.set(key, max_id)

    async def add_tracked_repo(self, user_id: str, repo_name: str, redis_client=None) -> None:
        """Add repository to the user's tracked set and increment global reference count."""
        client = redis_client or global_redis_client
        user_key = f"user:{user_id}:tracked_repos"
        is_member = await client.sismember(user_key, repo_name)
        if not is_member:
            await client.sadd(user_key, repo_name)
            ref_key = "global:tracked_repos_refcount"
            await client.hincrby(ref_key, repo_name, 1)
            global_key = "global:tracked_repos"
            await client.sadd(global_key, repo_name)

    async def get_tracked_repos(self, user_id: str, redis_client=None) -> list[str]:
        """Get repositories tracked by a specific user."""
        client = redis_client or global_redis_client
        user_key = f"user:{user_id}:tracked_repos"
        repos = await client.smembers(user_key)
        return list(repos)

    async def get_global_tracked_repos(self, redis_client=None) -> list[str]:
        """Get all repositories tracked by any user globally (for Celery polling)."""
        client = redis_client or global_redis_client
        global_key = "global:tracked_repos"
        repos = await client.smembers(global_key)
        return list(repos)

    async def remove_tracked_repo(self, user_id: str, repo_name: str, redis_client=None) -> None:
        """Remove repository from user's tracked set and decrement reference count.
        If reference count reaches 0, untrack globally and clean up cache/watermark.
        """
        client = redis_client or global_redis_client
        user_key = f"user:{user_id}:tracked_repos"
        is_member = await client.sismember(user_key, repo_name)
        if is_member:
            await client.srem(user_key, repo_name)
            ref_key = "global:tracked_repos_refcount"
            new_ref_count = await client.hincrby(ref_key, repo_name, -1)
            
            if new_ref_count <= 0:
                global_key = "global:tracked_repos"
                await client.srem(global_key, repo_name)
                await client.hdel(ref_key, repo_name)
                await client.delete(f"github:{repo_name}:max_id")
                await client.delete(f"github:{repo_name}:events")

    async def add_events(self, repo_name_or_map, events: list = None, redis_client=None) -> None:
        """Add new events to the repository's event list in Redis, keeping only the latest 100.
        Supports passing either (repo_name, events_list) or a batch dict {repo_name: events_list}.
        """
        if isinstance(repo_name_or_map, dict):
            for repo_name, evs in repo_name_or_map.items():
                await self._add_single_repo_events(repo_name, evs, redis_client=redis_client)
        else:
            await self._add_single_repo_events(repo_name_or_map, events, redis_client=redis_client)

    async def _add_single_repo_events(self, repo_name: str, new_events: list, redis_client=None) -> None:
        if not isinstance(new_events, list):
            return
            
        client = redis_client or global_redis_client
        key = f"github:{repo_name}:events"
        existing_data = await client.get(key)
        existing_events = json.loads(existing_data) if existing_data else []
        
        # Deduplicate based on event ID
        existing_ids = {event["id"] for event in existing_events if "id" in event}
        filtered_new = [event for event in new_events if event.get("id") not in existing_ids]
        
        # Prepend new events (since events are ordered newest first)
        combined_events = filtered_new + existing_events
        # Limit to the latest 100 events to prevent memory blow-up
        combined_events = combined_events[:100]
        
        await client.set(key, json.dumps(combined_events))

    async def get_events(self, repo_name: str, redis_client=None) -> list | None:
        """Retrieve cached events for a repository from Redis. Returns None if cache is cold/empty."""
        client = redis_client or global_redis_client
        key = f"github:{repo_name}:events"
        data = await client.get(key)
        return json.loads(data) if data is not None else None

repo_store_service = RepoStoreService()
