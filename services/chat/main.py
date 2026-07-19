import logging
import os
from contextlib import asynccontextmanager

import sentry_sdk
from dotenv import load_dotenv
from dynamo import dynamo_client
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sentry_sdk.integrations.fastapi import FastApiIntegration

from api.routes import router as http_router
from api.websockets import router as ws_router

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


# CORS configuration
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:5173,http://localhost:3000")
ALLOWED_ORIGINS = [origin.strip() for origin in CORS_ORIGINS.split(",")]


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown lifecycle."""
    # Startup
    creds_ok = await dynamo_client.verify_connection()
    if not creds_ok:
        logger.critical(
            "⚠️  DynamoDB credentials are INVALID. Chat persistence is DISABLED. "
            "Check AWS_ACCESS_KEY_ID / AWS_SECRET_ACCESS_KEY in 'backend-secrets' "
            "or configure IRSA for the chat pod."
        )
    else:
        try:
            await dynamo_client.create_table_if_not_exists()
            logger.info("DynamoDB table ready")
        except Exception as e:
            logger.error(f"Failed to initialize DynamoDB on startup: {e}")

    yield  # App is running

    # Shutdown (cleanup if needed)
    logger.info("Chat service shutting down")


# Initialize App
app = FastAPI(title="Chat Service", lifespan=lifespan)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    return {"status": "ok", "service": "chat"}


# Include Routers
# Default routes (for local Nginx stripping /api)
app.include_router(http_router)
# Production routes (for AWS ALB which does NOT strip /api)
app.include_router(http_router, prefix="/api")
app.include_router(ws_router)
