import asyncio
import json
import redis.asyncio as redis
from app.core.celery import celery_app
from app.core.config import settings
from app.services.githubService import github_service
from app.services.repoStoreService import repo_store_service

@celery_app.task
def poll_repo_events(repo_name: str):
    async def _poll():
        async with redis.from_url(settings.REDIS_URL, decode_responses=True) as local_redis:
            new_events = await github_service.get_new_repo_events(repo_name, redis_client=local_redis)
            if new_events:
                await repo_store_service.add_events(repo_name, new_events, redis_client=local_redis)
                channel = f"channel:events:{repo_name}"
                await local_redis.publish(channel, json.dumps(new_events))
            
    asyncio.run(_poll())

@celery_app.task
def poll_tracked_repositories_events():
    async def _poll_all():
        async with redis.from_url(settings.REDIS_URL, decode_responses=True) as local_redis:
            repos = await repo_store_service.get_global_tracked_repos(redis_client=local_redis)
            for repo in repos:
                poll_repo_events.delay(repo)
            
    asyncio.run(_poll_all())