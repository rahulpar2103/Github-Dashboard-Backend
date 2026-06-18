import asyncio
import json
from celery.signals import worker_process_init, worker_process_shutdown
from app.core.celery import celery_app
from app.core.redis import redis_client
from app.services.githubService import github_service
from app.services.repoStoreService import repo_store_service

worker_loop = None

@worker_process_init.connect
def init_worker_process(**kwargs):
    global worker_loop
    worker_loop = asyncio.new_event_loop()
    asyncio.set_event_loop(worker_loop)

@worker_process_shutdown.connect
def shutdown_worker_process(**kwargs):
    global worker_loop
    if worker_loop and not worker_loop.is_closed():
        worker_loop.close()

def run_async_task(coro):
    global worker_loop
    if worker_loop is None or worker_loop.is_closed():
        return asyncio.run(coro)
    return worker_loop.run_until_complete(coro)

@celery_app.task
def poll_repo_events(repo_name: str):
    async def _poll():
        new_events = await github_service.get_new_repo_events(repo_name)
        if new_events:
            await repo_store_service.add_events(repo_name, new_events)
            channel = f"channel:events:{repo_name}"
            await redis_client.publish(channel, json.dumps(new_events))
            
    run_async_task(_poll())

@celery_app.task
def poll_tracked_repositories_events():
    async def _poll_all():
        repos = await repo_store_service.get_global_tracked_repos()
        for repo in repos:
            poll_repo_events.delay(repo)
            
    run_async_task(_poll_all())