import asyncio
import json
from app.core.celery import celery_app
from app.core.redis import redis_client
from app.services.githubService import github_service
from app.services.repoStoreService import repo_store_service

@celery_app.task
def poll_repo_events(repo_name: str):
    async def _poll():
        new_events = await github_service.get_new_repo_events(repo_name)
        if new_events:
            await repo_store_service.add_events(repo_name, new_events)
            channel = f"channel:events:{repo_name}"
            await redis_client.publish(channel, json.dumps(new_events))
            
    asyncio.run(_poll())

@celery_app.task
def poll_tracked_repositories_events():
    async def _poll_all():
        repos = await repo_store_service.get_global_tracked_repos()
        for repo in repos:
            poll_repo_events.delay(repo)
            
    asyncio.run(_poll_all())