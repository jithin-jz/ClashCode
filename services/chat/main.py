import logging
import os

import sentry_sdk
from api.routes import router as http_router
from api.websockets import router as ws_router
from dotenv import load_dotenv
from dynamo import dynamo_client
from fastapi import FastAPI, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
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
    logger.info("Sentry initialized for Chat service")

# Initialize App
app = FastAPI(title="Chat Service")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def on_startup():
    try:
        await dynamo_client.create_table_if_not_exists()
        logger.info("DynamoDB table ready")
    except Exception as e:
        logger.error(f"Failed to initialize DynamoDB on startup: {e}")


# Include Routers
app.include_router(http_router)
app.include_router(ws_router)


# Global Exception Handler
@app.exception_handler(Exception)
async def global_exception_handler(request, exc: Exception):
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        content={"error": "Internal server error"},
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8002)
