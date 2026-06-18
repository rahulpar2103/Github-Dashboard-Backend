from app.core.redis import redis_client
import json


class RepoStoreService:
    async def get_max_id(self, repo_name: str) -> int:
        key = f"github:{repo_name}:max_id"
        max_id = await redis_client.get(key)
        return int(max_id) if max_id else 0

    async def set_max_id(self, repo_name: str, max_id: int):
        key = f"github:{repo_name}:max_id"
        await redis_client.set(key, max_id)

    async def add_tracked_repo(self, user_id: str, repo_name: str) -> None:
        user_key = f"user:{user_id}:tracked_repos"
        is_member = await redis_client.sismember(user_key, repo_name)
        if not is_member:
            await redis_client.sadd(user_key, repo_name)
            ref_key = "global:tracked_repos_refcount"
            await redis_client.hincrby(ref_key, repo_name, 1)
            await redis_client.sadd("global:tracked_repos", repo_name)

    async def get_tracked_repos(self, user_id: str) -> list[str]:
        user_key = f"user:{user_id}:tracked_repos"
        repos = await redis_client.smembers(user_key)
        return list(repos)

    async def get_global_tracked_repos(self) -> list[str]:
        repos = await redis_client.smembers("global:tracked_repos")
        return list(repos)

    async def remove_tracked_repo(self, user_id: str, repo_name: str) -> None:
        user_key = f"user:{user_id}:tracked_repos"
        is_member = await redis_client.sismember(user_key, repo_name)
        if is_member:
            await redis_client.srem(user_key, repo_name)
            ref_key = "global:tracked_repos_refcount"
            new_ref_count = await redis_client.hincrby(ref_key, repo_name, -1)
            if new_ref_count <= 0:
                await redis_client.srem("global:tracked_repos", repo_name)
                await redis_client.hdel(ref_key, repo_name)
                await redis_client.delete(f"github:{repo_name}:max_id")
                await redis_client.delete(f"github:{repo_name}:events")

    async def add_events(self, repo_name: str, events: list) -> None:
        if not isinstance(events, list):
            return
        key = f"github:{repo_name}:events"
        existing_data = await redis_client.get(key)
        existing_events = json.loads(existing_data) if existing_data else []
        existing_ids = {event["id"] for event in existing_events if "id" in event}
        filtered_new = [event for event in events if event.get("id") not in existing_ids]
        combined = (filtered_new + existing_events)[:100]
        await redis_client.set(key, json.dumps(combined))

    async def get_events(self, repo_name: str) -> list | None:
        key = f"github:{repo_name}:events"
        data = await redis_client.get(key)
        return json.loads(data) if data is not None else None


repo_store_service = RepoStoreService()
