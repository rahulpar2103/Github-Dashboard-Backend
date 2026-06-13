from app.core.redis import redis_client

class RepoStoreService:
    async def get_max_id(self, repo_name: str) -> int:
        key = f"0:{repo_name}:max_id"
        max_id = await redis_client.get(key)
        if max_id:
            return int(max_id)
        return 0

    async def set_max_id(self, repo_name: str, max_id: int):
        key = f"0:{repo_name}:max_id"
        await redis_client.set(key, max_id)

    async def add_tracked_repo(self, repo_name: str) -> None:
        key = "0:tracked_repos"
        await redis_client.sadd(key, repo_name)

    async def get_tracked_repos(self) -> list[str]:
        key = "0:tracked_repos"
        repos = await redis_client.smembers(key)
        return list(repos)

repo_store_service = RepoStoreService()

