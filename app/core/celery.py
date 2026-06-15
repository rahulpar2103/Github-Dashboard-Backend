from celery import Celery
from app.core.config import settings

celery_app = Celery(
    "github_dashboard",
    backend=settings.REDIS_URL,
    broker=settings.REDIS_URL,
    include=["app.tasks"]
)

celery_app.conf.beat_schedule = {
    "poll-tracked-repositories-every-10-seconds": {
        "task": "app.tasks.poll_tracked_repositories_events",
        "schedule": 10.0,
    },
}
celery_app.conf.timezone = "UTC"
celery_app.conf.broker_connection_retry_on_startup = True