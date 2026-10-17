import logging
import os

import jwt
from fastapi import Request, WebSocket

from utils.redis_client import redis_client

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

ALLOWED_ORIGINS = [
    origin.strip()
    for origin in os.getenv("CORS_ORIGINS", "http://localhost:5173,http://localhost:3000").split(",")
    if origin.strip()
]

# Written by core (authentication/revocation.py) on logout, refresh rotation and account disable.
REVOKED_JTI_KEY = "auth:revoked_jti:{jti}"
DISABLED_USER_KEY = "auth:disabled_user:{user_id}"


def get_token(request: Request | WebSocket) -> str | None:
    """
    Bearer header or the HttpOnly access-token cookie.

    Tokens in query strings are deliberately not accepted: URLs end up in proxy
    and load-balancer access logs.
    """
    token = None
    auth = request.headers.get("authorization")
    if auth and auth.lower().startswith("bearer "):
        token = auth.split(" ", 1)[1]

    if not token:
        token = request.cookies.get(JWT_ACCESS_COOKIE_NAME)
    return token


def is_origin_allowed(ws: WebSocket) -> bool:
    """
    Blocks cross-site WebSocket hijacking: browsers always send Origin and attach
    cookies, so a foreign page must not be able to open a socket as the user.
    Non-browser clients send no Origin and authenticate with a Bearer header.
    """
    origin = ws.headers.get("origin")
    if not origin:
        return True
    return "*" in ALLOWED_ORIGINS or origin.rstrip("/") in {o.rstrip("/") for o in ALLOWED_ORIGINS}


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


async def is_revoked(payload: dict) -> bool:
    """True when core revoked this token (logout) or disabled the account."""
    keys = [DISABLED_USER_KEY.format(user_id=payload.get("user_id"))]
    if payload.get("jti"):
        keys.append(REVOKED_JTI_KEY.format(jti=payload["jti"]))
    try:
        return bool(await redis_client.exists(*keys))
    except Exception:
        # Fail open: with Redis down chat cannot deliver messages anyway, and the
        # token signature and expiry were already verified.
        logger.exception("Revocation check failed")
        return False
