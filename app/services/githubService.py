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

github_service=GithubService()