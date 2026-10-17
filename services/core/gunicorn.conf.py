"""Gunicorn settings for the core API (used by the Docker image and compose)."""

import os

bind = f"0.0.0.0:{os.getenv('PORT', '8000')}"

# Threaded workers: requests that wait on I/O (DB, Redis, the AI streaming proxy)
# no longer block the whole worker the way the default single sync worker did.
worker_class = "gthread"
workers = int(os.getenv("GUNICORN_WORKERS", "3"))
threads = int(os.getenv("GUNICORN_THREADS", "4"))

# Above the 60s AI streaming proxy timeout so streams are not cut off.
timeout = int(os.getenv("GUNICORN_TIMEOUT", "90"))
graceful_timeout = int(os.getenv("GUNICORN_GRACEFUL_TIMEOUT", "30"))
keepalive = 5

# Recycle workers periodically to contain slow memory leaks.
max_requests = int(os.getenv("GUNICORN_MAX_REQUESTS", "1000"))
max_requests_jitter = 100

# Heartbeat files on tmpfs: the container root filesystem is read-only.
worker_tmp_dir = "/dev/shm"

accesslog = "-"
errorlog = "-"
loglevel = os.getenv("GUNICORN_LOG_LEVEL", "info")
