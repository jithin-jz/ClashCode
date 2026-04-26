import logging
import os

import sentry_sdk
from api.routes import router as executor_router
from dotenv import load_dotenv
from fastapi import FastAPI
from sentry_sdk.integrations.fastapi import FastApiIntegration

# Load Environment
load_dotenv()

# Configure Logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Sentry initialization
SENTRY_DSN = os.getenv("SENTRY_DSN")
if SENTRY_DSN:
    sentry_sdk.init(
        dsn=SENTRY_DSN,
        traces_sample_rate=1.0,
        profiles_sample_rate=1.0,
        environment=os.getenv("ENVIRONMENT", "development"),
        integrations=[FastApiIntegration()],
    )
    logger.info("Sentry initialized for Executor service")

# Initialize App
app = FastAPI(title="CLASHCODE Python Executor", version="1.1")

# Include Routers
app.include_router(executor_router)

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8003)
