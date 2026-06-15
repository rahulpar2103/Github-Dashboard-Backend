import asyncio
import json
import redis.asyncio as redis
from app.core.celery import celery_app
from app.core.config import settings
from app.services.githubService import github_service
from app.services.repoStoreService import repo_store_service

@celery_app.task
def poll_repo_events(repo_name: str):
    """Poll a single repository for new events, saves them, and publish to Pub/Sub."""
    async def _poll():
        # Create a local, task-isolated async Redis client
        async with redis.from_url(settings.REDIS_URL, decode_responses=True) as local_redis:
            # Fetch only new events, passing the local client
            new_events = await github_service.get_new_repo_events(repo_name, redis_client=local_redis)
            if new_events:
                # 1. Save new events in Redis storage (appends and caps to 100)
                await repo_store_service.add_events(repo_name, new_events, redis_client=local_redis)
                
                # 2. Publish to Pub/Sub channel to notify active WebSockets
                channel = f"channel:events:{repo_name}"
                await local_redis.publish(channel, json.dumps(new_events))
            
    # Run the async function in a synchronous context
    asyncio.run(_poll())

@celery_app.task
def poll_tracked_repositories_events():
    """Periodic task that initiates polling for all tracked repositories."""
    async def _poll_all():
        # Create a local, task-isolated async Redis client
        async with redis.from_url(settings.REDIS_URL, decode_responses=True) as local_redis:
            # Poll all repositories tracked by any user globally
            repos = await repo_store_service.get_global_tracked_repos(redis_client=local_redis)
            for repo in repos:
                # Dispatch individual Celery tasks for each repo to process in parallel
                poll_repo_events.delay(repo)
            
    asyncio.run(_poll_all())