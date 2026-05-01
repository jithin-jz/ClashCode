import logging
import os

import httpx
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Configure Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="CLASHCODE Analytics Service")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

PROMETHEUS_URL = os.getenv("PROMETHEUS_URL", "http://prometheus-server.monitoring.svc.cluster.local")


@app.get("/health")
def health():
    return {"status": "ok", "service": "analytics"}


@app.get("/stats/cluster")
async def get_cluster_stats():
    """
    Proxies specific metrics from Prometheus to the Admin Dashboard.
    This keeps the Prometheus API secure and provides a clean interface for the UI.
    """
    try:
        async with httpx.AsyncClient() as client:
            # Query for Total Pod Memory Usage
            mem_query = 'sum(container_memory_usage_bytes{namespace="default"})'
            cpu_query = 'sum(rate(container_cpu_usage_seconds_total{namespace="default"}[5m]))'

            mem_response = await client.get(f"{PROMETHEUS_URL}/api/v1/query", params={"query": mem_query})
            cpu_response = await client.get(f"{PROMETHEUS_URL}/api/v1/query", params={"query": cpu_query})

            return {
                "memory_usage_bytes": (
                    mem_response.json()["data"]["result"][0]["value"][1] if mem_response.status_code == 200 else 0
                ),
                "cpu_usage_cores": (
                    cpu_response.json()["data"]["result"][0]["value"][1] if cpu_response.status_code == 200 else 0
                ),
                "status": "healthy",
            }
    except Exception as e:
        logger.error(f"Failed to fetch Prometheus metrics: {e}")
        return {"status": "degraded", "error": str(e)}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8004)
