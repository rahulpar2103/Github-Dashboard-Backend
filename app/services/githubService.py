from app.core.config import settings
import httpx
from app.services.repoStoreService import repo_store_service

class GithubService:
    def __init__(self):
        self.client = None

    def get_http_client(self) -> httpx.AsyncClient:
        if self.client is None or self.client.is_closed:
            self.client = httpx.AsyncClient(follow_redirects=True)
        return self.client

    def init_client(self):
        self.get_http_client()

    async def close(self):
        if self.client is not None and not self.client.is_closed:
            await self.client.aclose()



    async def get_repo_events(self, repo_name: str, token: str = None) -> list:
        client = self.get_http_client()
        headers = {}
        github_token = token or settings.GITHUB_TOKEN
        if github_token:
            headers["Authorization"] = f"token {github_token}"
            
        url = f"https://api.github.com/repos/{repo_name}/events"
        try:
            resp = await client.get(url, headers=headers)
            if resp.status_code == 200:
                return resp.json()
            return []
        except Exception:
            return []

    async def get_new_repo_events(self, repo_name: str) -> list:
        max_id = await repo_store_service.get_max_id(repo_name)
        events = await self.get_repo_events(repo_name)
        if not isinstance(events, list):
            return []
        filtered_events = [event for event in events if int(event.get("id", 0)) > max_id]
        if filtered_events:
            new_max_id = max([int(event["id"]) for event in filtered_events if "id" in event])
            await repo_store_service.set_max_id(repo_name, new_max_id)
        return filtered_events

    async def track_repository(self, repo_name: str, user_id: str) -> list:
        await repo_store_service.add_tracked_repo(user_id, repo_name)
        events = await self.get_repo_events(repo_name)
        if isinstance(events, list) and events:
            max_id = max([int(event["id"]) for event in events if "id" in event])
            await repo_store_service.set_max_id(repo_name, max_id)
            await repo_store_service.add_events(repo_name, events)
        else:
            await repo_store_service.add_events(repo_name, [])
        return events

    async def get_tracked_repositories_events_cached(self, user_id: str) -> dict[str, list]:
        repos = await repo_store_service.get_tracked_repos(user_id)
        results = {}
        for repo in repos:
            events = await repo_store_service.get_events(repo)
            if events is None:
                events = await self.track_repository(repo, user_id=user_id)
            results[repo] = events
        return results

    async def untrack_repository(self, repo_name: str, user_id: str) -> None:
        await repo_store_service.remove_tracked_repo(user_id, repo_name)

    async def get_repository_events_with_watermark(self, repo_name: str, user_id: str) -> list:
        events = await repo_store_service.get_events(repo_name)
        if events is None:
            events = await self.track_repository(repo_name, user_id=user_id)
        return events

github_service = GithubService()