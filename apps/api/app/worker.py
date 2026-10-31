from celery import Celery

from app.core.config import get_settings
from app.jobs.registry import BEAT_SCHEDULE

celery_app = Celery("yep_portal", broker=get_settings().celery_broker_url)
celery_app.conf.update(
    beat_schedule=BEAT_SCHEDULE,
    task_serializer="json",
    accept_content=["json"],
    timezone="UTC",
)
celery_app.autodiscover_tasks(["app"])
