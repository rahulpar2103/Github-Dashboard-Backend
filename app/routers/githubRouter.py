from fastapi import APIRouter
from app.services.githubService import github_service

router=APIRouter(prefix="/github", tags=["GitHub"])

@router.get("/{repo_name:path}/events")
async def get_repo_events(repo_name: str):
    events=await github_service.get_repo_events(repo_name)
    return events
