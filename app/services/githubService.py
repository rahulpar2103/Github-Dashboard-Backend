from app.core.config import settings
import httpx
class GithubService:
    
    async def get_repo_events(self, repo_name: str):
        async with httpx.AsyncClient() as client:
            headers = {
                "Authorization": f"token {settings.GITHUB_TOKEN}"
            }

            url = f"https://api.github.com/repos/{repo_name}/events"

            resp = await client.get(url, headers=headers)
            return resp.json()

github_service=GithubService()