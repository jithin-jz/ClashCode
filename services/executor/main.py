import logging
import os

from dotenv import load_dotenv

# Load Environment before importing modules that read configuration at import time
load_dotenv()

import sentry_sdk  # noqa: E402
from fastapi import FastAPI  # noqa: E402
from sentry_sdk.integrations.fastapi import FastApiIntegration  # noqa: E402

from api.routes import router as executor_router  # noqa: E402
from core.auth import auth_configuration_error  # noqa: E402

# Configure Logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Sentry initialization
SENTRY_DSN = os.getenv("SENTRY_DSN")
if SENTRY_DSN:
    sentry_sdk.init(
        dsn=SENTRY_DSN,
        traces_sample_rate=float(os.getenv("SENTRY_TRACES_SAMPLE_RATE", "0.1")),
        profiles_sample_rate=float(os.getenv("SENTRY_PROFILES_SAMPLE_RATE", "0")),
        send_default_pii=False,
        environment=os.getenv("ENVIRONMENT", "development"),
        integrations=[FastApiIntegration()],
    )
    logger.info("Sentry initialized for Executor service")

_auth_error = auth_configuration_error()
if _auth_error:
    logger.error(f"Executor auth is misconfigured and will reject every /execute call: {_auth_error}")

# Initialize App
app = FastAPI(title="CLASHCODE Python Executor", version="2.0", docs_url=None, redoc_url=None)

# Include Routers
app.include_router(executor_router)

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8011)
