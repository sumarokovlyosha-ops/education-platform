from celery import Celery

from app.core.config import get_celery_settings

settings = get_celery_settings()

celery_app = Celery(
    "education_platform",
    broker=settings.broker_url.get_secret_value(),
    backend=settings.result_backend.get_secret_value(),
    include=["app.tasks.health"],
)


celery_app.conf.update(
    task_default_queue="education_platform",
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    result_accept_content=["json"],
    result_expires=settings.result_expires,
    timezone="UTC",
    enable_utc=True,
    broker_connection_retry_on_startup=True,
)
