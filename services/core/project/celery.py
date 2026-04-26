import logging
import os

from celery import Celery

# Set the default Django settings module for the 'celery' program.
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "project.settings")

app = Celery("project")

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
# - namespace='CELERY' means all celery-related configuration keys
#   should have a `CELERY_` prefix.
app.config_from_object("django.conf:settings", namespace="CELERY")

# Load task modules from all registered Django apps.
app.autodiscover_tasks()

# Also discover tasks from the project package itself (project/tasks.py)
app.autodiscover_tasks(["project"])

logger = logging.getLogger(__name__)


@app.task(bind=True)
def debug_task(self):
    """Debug task that stores its result in the result backend."""
    logger.info("Request: %r", self.request)
    return {"status": "ok", "worker": self.request.hostname}
