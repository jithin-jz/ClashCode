import logging
from datetime import timedelta

from celery import shared_task
from django.utils import timezone

logger = logging.getLogger(__name__)


@shared_task(name="project.tasks.cleanup_old_task_results")
def cleanup_old_task_results():
    """
    Periodic task to purge Celery task results older than 7 days
    from the django_celery_results database table.
    Keeps the results table from growing unbounded.
    """
    from django_celery_results.models import TaskResult

    cutoff = timezone.now() - timedelta(days=7)
    deleted_count, _ = TaskResult.objects.filter(date_done__lt=cutoff).delete()
    logger.info("Cleaned up %d old task result(s) (older than %s)", deleted_count, cutoff)
    return {"deleted": deleted_count, "cutoff": str(cutoff)}
