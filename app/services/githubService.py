from app.core.config import settings
import httpx
import asyncio
from app.services.repoStoreService import repo_store_service

class GithubService:
    def __init__(self):
        self.client = None

    def init_client(self):
        if self.client is None or self.client.is_closed:
            self.client = httpx.AsyncClient(follow_redirects=True)

    async def close(self):
        if self.client is not None and not self.client.is_closed:
            await self.client.aclose()

    async def get_repo_events(self, repo_name: str, client: httpx.AsyncClient = None):
        # Determine the active client: passed > shared > none (create local client)
        active_client = client or self.client
        
        headers = {
            "Authorization": f"token {settings.GITHUB_TOKEN}"
        }
        url = f"https://api.github.com/repos/{repo_name}/events"

        if active_client is not None:
            resp = await active_client.get(url, headers=headers)
            return resp.json()
            
        async with httpx.AsyncClient(follow_redirects=True) as local_client:
            resp = await local_client.get(url, headers=headers)
            return resp.json()

    async def get_new_repo_events(self, repo_name: str, client: httpx.AsyncClient = None) -> list:
        max_id = await repo_store_service.get_max_id(repo_name)
        events = await self.get_repo_events(repo_name, client=client)
        if not isinstance(events, list):
            return []
        filtered_events = [event for event in events if int(event["id"]) > max_id]
        if filtered_events:
            new_max_id = max([int(event["id"]) for event in filtered_events])
            await repo_store_service.set_max_id(repo_name, new_max_id)
        return filtered_events

    async def track_repository(self, repo_name: str, client: httpx.AsyncClient = None) -> list:
        await repo_store_service.add_tracked_repo(repo_name)
        events = await self.get_repo_events(repo_name, client=client)
        if isinstance(events, list) and events:
            max_id = max([int(event["id"]) for event in events if "id" in event])
            await repo_store_service.set_max_id(repo_name, max_id)
            # Cache the initial events
            await repo_store_service.add_events(repo_name, events)
        return events

    async def get_tracked_repositories_events(self, client: httpx.AsyncClient = None) -> dict[str, list]:
        repos = await repo_store_service.get_tracked_repos()
        active_client = client or self.client
        
        if active_client is not None:
            tasks = [self.get_repo_events(repo, client=active_client) for repo in repos]
            events_list = await asyncio.gather(*tasks)
        else:
            async with httpx.AsyncClient(follow_redirects=True) as local_client:
                tasks = [self.get_repo_events(repo, client=local_client) for repo in repos]
                events_list = await asyncio.gather(*tasks)
                
        return {repo: events for repo, events in zip(repos, events_list)}

    async def get_tracked_repositories_events_cached(self, client: httpx.AsyncClient = None) -> dict[str, list]:
        repos = await repo_store_service.get_tracked_repos()
        results = {}
        for repo in repos:
            events = await repo_store_service.get_events(repo)
            if not events:
                events = await self.track_repository(repo, client=client)
            results[repo] = events
        return results

    async def untrack_repository(self, repo_name: str) -> None:
        await repo_store_service.remove_tracked_repo(repo_name)

    async def get_repository_events_with_watermark(self, repo_name: str, client: httpx.AsyncClient = None) -> list:
        events = await repo_store_service.get_events(repo_name)
        if not events:
            events = await self.track_repository(repo_name, client=client)
        return events

github_service = GithubService()