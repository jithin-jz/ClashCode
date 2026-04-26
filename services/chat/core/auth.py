import logging
import os

import jwt
from fastapi import Request, WebSocket

logger = logging.getLogger(__name__)

# JWT Configuration
ALGORITHM = os.getenv("JWT_ALGORITHM", "RS256").upper()
JWT_PUBLIC_KEY = os.getenv("JWT_PUBLIC_KEY", "").replace("\\n", "\n").strip()
JWT_SHARED_SECRET = os.getenv("JWT_SHARED_SECRET", "").strip() or os.getenv("SECRET_KEY", "").strip()
JWT_VERIFY_KEY = JWT_PUBLIC_KEY
if not JWT_VERIFY_KEY and JWT_SHARED_SECRET:
    ALGORITHM = "HS256"
    JWT_VERIFY_KEY = JWT_SHARED_SECRET
JWT_ACCESS_COOKIE_NAME = os.getenv("JWT_ACCESS_COOKIE_NAME", "access_token")


def get_token(request: Request | WebSocket) -> str | None:
    token = None
    auth = request.headers.get("authorization")
    if auth and auth.lower().startswith("bearer "):
        token = auth.split(" ", 1)[1]

    if not token and hasattr(request, "query_params"):
        token = request.query_params.get("token")

    if not token:
        token = request.cookies.get(JWT_ACCESS_COOKIE_NAME)
    return token


def verify_jwt(token: str) -> dict | None:
    if not token:
        return None
    if not JWT_VERIFY_KEY:
        logger.warning("JWT verification key is not configured for the chat service.")
        return None
    try:
        payload = jwt.decode(
            token,
            JWT_VERIFY_KEY,
            algorithms=[ALGORITHM],
            options={"require": ["exp"]},
        )
        if payload.get("type") != "access" or "user_id" not in payload:
            return None
        return payload
    except jwt.PyJWTError:
        return None
