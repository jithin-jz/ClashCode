import logging

import httpx
from config import settings
from core.security import build_internal_headers
from fastapi import HTTPException

logger = logging.getLogger(__name__)


async def fetch_challenge_context(challenge_slug: str):
    try:
        path = f"/api/challenges/{challenge_slug}/context/"
        url = f"{settings.CORE_SERVICE_URL}{path}"
        headers = build_internal_headers(path)
        logger.info(f"Fetching context from: {url}")
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers, timeout=5)
            if response.status_code != 200:
                logger.error(f"Core service error: {response.status_code} - {response.text}")
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"Core service returned {response.status_code}",
                )
            return response.json()
    except httpx.RequestError as e:
        logger.error(f"Error connecting to Core Service: {e}")
        raise HTTPException(status_code=503, detail="Core service unavailable")


async def fetch_internal_challenges():
    """Fetch all challenges from Core for indexing."""
    path = "/api/challenges/internal-list/"
    url = f"{settings.CORE_SERVICE_URL}{path}"
    headers = build_internal_headers(path)

    async with httpx.AsyncClient() as client:
        try:
            resp = await client.get(url, headers=headers, timeout=10)
            if resp.status_code != 200:
                logger.error(f"Failed to fetch challenges for indexing: {resp.text}")
                return None
            return resp.json()
        except Exception as e:
            logger.error(f"Error connecting to Core for indexing: {e}")
            return None
