import logging

import sentry_sdk
from api.routes import router as ai_router
from config import settings
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from logger_config import setup_logging
from sentry_sdk.integrations.fastapi import FastApiIntegration

# Load Environment
load_dotenv()

# Configure Logging
setup_logging()
logger = logging.getLogger(__name__)

# Sentry Configuration
if settings.SENTRY_DSN:
    sentry_sdk.init(
        dsn=settings.SENTRY_DSN,
        integrations=[FastApiIntegration()],
        traces_sample_rate=1.0 if settings.DEBUG else 0.2,
        send_default_pii=True,
        environment=settings.ENVIRONMENT,
    )

# Initialize App
app = FastAPI(
    title="AI Service",
    version="1.0",
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routes
app.include_router(ai_router)


# Global Exception Handler
@app.exception_handler(Exception)
async def global_exception_handler(request, exc: Exception):
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8002)
