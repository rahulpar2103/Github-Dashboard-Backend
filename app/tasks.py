import asyncio
import json
import redis
from app.core.celery import celery_app
from app.core.config import settings
from app.services.githubService import github_service
from app.services.repoStoreService import repo_store_service

# Initialize a synchronous Redis client for Celery tasks to avoid loop-binding issues
sync_redis = redis.from_url(settings.REDIS_URL, decode_responses=True)

@celery_app.task
def poll_repo_events(repo_name: str):
    """Poll a single repository for new events, save them, and publish to Pub/Sub."""
    async def _poll():
        # Fetch only new events (compares against max_id and updates max_id)
        new_events = await github_service.get_new_repo_events(repo_name)
        if new_events:
            # 1. Save new events in Redis storage (appends and caps to 100)
            await repo_store_service.add_events(repo_name, new_events)
            
            # 2. Publish to Pub/Sub channel to notify active WebSockets
            channel = f"channel:events:{repo_name}"
            sync_redis.publish(channel, json.dumps(new_events))
            
    # Run the async function in a synchronous context
    asyncio.run(_poll())

@celery_app.task
def poll_tracked_repositories_events():
    """Periodic task that initiates polling for all tracked repositories."""
    async def _poll_all():
        repos = await repo_store_service.get_tracked_repos()
        for repo in repos:
            # Dispatch individual Celery tasks for each repo to process in parallel
            poll_repo_events.delay(repo)
            
    asyncio.run(_poll_all())