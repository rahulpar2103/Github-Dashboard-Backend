from fastapi import APIRouter
from app.schemas.github import TrackRepoRequest, UntrackRepoRequest
from app.services.githubService import github_service

router=APIRouter(prefix="/github", tags=["GitHub"])

@router.post("/track")
async def track_repo(request: TrackRepoRequest):
    events = await github_service.track_repository(request.repo)
    return {
        "status": "success",
        "message": f"Started tracking {request.repo}",
        "events": events
    }

@router.get("/tracked")
async def get_tracked_repos():
    results = await github_service.get_tracked_repositories_events_cached()
    return {"tracked_repositories": results}

@router.delete("/track")
async def untrack_repo(request: UntrackRepoRequest):
    await github_service.untrack_repository(request.repo)
    return {
        "status": "success",
        "message": f"Stopped tracking {request.repo}"
    }


@router.get("/{repo_name:path}/events")
async def get_repo_events(repo_name: str):
    events = await github_service.get_repository_events_with_watermark(repo_name)
    return events


