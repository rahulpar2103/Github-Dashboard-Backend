from app.core.config import settings
import httpx
from app.services.repoStoreService import repo_store_service

class GithubService:
    async def get_repo_events(self, repo_name: str):
        async with httpx.AsyncClient(follow_redirects=True) as client:
            headers = {
                "Authorization": f"token {settings.GITHUB_TOKEN}"
            }

            url = f"https://api.github.com/repos/{repo_name}/events"

            resp = await client.get(url, headers=headers)
            return resp.json()

    async def get_new_repo_events(self, repo_name: str) -> list:
        max_id = await repo_store_service.get_max_id(repo_name)
        events = await self.get_repo_events(repo_name)
        if not isinstance(events, list):
            return []
        filtered_events = [event for event in events if int(event["id"]) > max_id]
        if filtered_events:
            new_max_id = max([int(event["id"]) for event in filtered_events])
            await repo_store_service.set_max_id(repo_name, new_max_id)
        return filtered_events

    async def track_repository(self, repo_name: str) -> list:
        await repo_store_service.add_tracked_repo(repo_name)
        events = await self.get_repo_events(repo_name)
        if isinstance(events, list) and events:
            max_id = max([int(event["id"]) for event in events if "id" in event])
            await repo_store_service.set_max_id(repo_name, max_id)
        return events

    async def get_tracked_repositories_events(self) -> dict[str, list]:
        repos = await repo_store_service.get_tracked_repos()
        results = {}
        for repo in repos:
            events = await self.get_repo_events(repo)
            results[repo] = events
        return results

    async def untrack_repository(self, repo_name: str) -> None:
        await repo_store_service.remove_tracked_repo(repo_name)

    async def get_repository_events_with_watermark(self, repo_name: str) -> list:
        return await self.track_repository(repo_name)

github_service=GithubService()