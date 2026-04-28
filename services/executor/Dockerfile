# syntax=docker/dockerfile:1.7
FROM python:3.12-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app
COPY requirements.txt ./
RUN pip install --prefix=/install -r requirements.txt

FROM python:3.12-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/install/bin:$PATH" \
    PYTHONPATH="/install/lib/python3.12/site-packages"

RUN apt-get update && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/* \
    && useradd --create-home --uid 10001 executor

WORKDIR /app
COPY --from=builder /install /install
COPY --chown=executor:executor main.py /app/
COPY --chown=executor:executor api/ /app/api/
COPY --chown=executor:executor core/ /app/core/
COPY --chown=executor:executor models/ /app/models/
COPY --chown=executor:executor services/ /app/services/
COPY --chown=executor:executor utils/ /app/utils/

USER executor
EXPOSE 8011

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=5 \
    CMD curl -fsS http://127.0.0.1:8011/health || exit 1

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8011"]
