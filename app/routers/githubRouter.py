from fastapi import APIRouter
from pydantic import BaseModel
from app.services.githubService import github_service
from app.services.repoStoreService import repo_store_service

router=APIRouter(prefix="/github", tags=["GitHub"])

class TrackRepoRequest(BaseModel):
    repo: str

@router.post("/track")
async def track_repo(request: TrackRepoRequest):
    await repo_store_service.add_tracked_repo(request.repo)
    events = await github_service.get_new_repo_events(request.repo)
    return {
        "status": "success",
        "message": f"Started tracking {request.repo}",
        "events": events
    }

@router.get("/tracked")
async def get_tracked_repos():
    repos = await repo_store_service.get_tracked_repos()
    return {"tracked_repositories": repos}

@router.get("/{repo_name:path}/events")
async def get_repo_events(repo_name: str):
    await repo_store_service.add_tracked_repo(repo_name)
    events = await github_service.get_new_repo_events(repo_name)
    return events

