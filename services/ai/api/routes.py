import asyncio
import logging
from typing import Optional

from config import settings
from core.ai_logic import analyze_code_logic, generate_hint_logic
from core.rag import get_vector_db
from core.security import authorize_internal_request
from fastapi import APIRouter, Header, HTTPException, Request
from langchain_core.documents import Document
from models.schemas import AnalyzeRequest, HintRequest
from utils.core_client import fetch_challenge_context, fetch_internal_challenges

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/health")
def health():
    return {"status": "ok"}


@router.post("/index")
async def index_challenges(
    http_request: Request,
    x_internal_api_key: Optional[str] = Header(None, alias="X-Internal-API-Key"),
    x_internal_timestamp: Optional[str] = Header(None, alias="X-Internal-Timestamp"),
    x_internal_signature: Optional[str] = Header(None, alias="X-Internal-Signature"),
):
    if not authorize_internal_request(
        path=http_request.url.path,
        api_key=x_internal_api_key,
        timestamp=x_internal_timestamp,
        signature=x_internal_signature,
    ):
        raise HTTPException(status_code=403, detail="Unauthorized")

    logger.info("Starting challenge indexing (RAG pre-warming)...")

    challenges = await fetch_internal_challenges()
    if challenges is None:
        return {"status": "error", "detail": "Core service fetch failed"}

    vdb = get_vector_db()
    if vdb is None:
        return {"status": "error", "detail": "Vector DB initialization failed"}

    docs = []
    for c in challenges:
        content = f"Title: {c.get('title')}\nDescription: {c.get('description')}\nInitial Code:\n{c.get('initial_code')}\n"
        docs.append(
            Document(
                page_content=content,
                metadata={"slug": c.get("slug"), "type": "challenge_context"},
            )
        )

    try:
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(None, lambda: vdb.add_documents(docs))
        logger.info(f"Successfully indexed {len(docs)} challenges.")
        return {"status": "ok", "indexed_count": len(docs)}
    except Exception as e:
        logger.error(f"Failed to add documents to Chroma: {e}")
        return {"status": "error", "detail": "Chroma storage failed"}


@router.post("/hints")
async def generate_hint(
    request: HintRequest,
    http_request: Request,
    x_internal_api_key: Optional[str] = Header(None, alias="X-Internal-API-Key"),
    x_internal_timestamp: Optional[str] = Header(None, alias="X-Internal-Timestamp"),
    x_internal_signature: Optional[str] = Header(None, alias="X-Internal-Signature"),
):
    if not authorize_internal_request(
        path=http_request.url.path,
        api_key=x_internal_api_key,
        timestamp=x_internal_timestamp,
        signature=x_internal_signature,
    ):
        raise HTTPException(status_code=403, detail="Unauthorized")

    if not settings.GROQ_API_KEY:
        raise HTTPException(status_code=500, detail="LLM API Key not configured")

    context_data = await fetch_challenge_context(request.challenge_slug)

    try:
        safe_hint = await generate_hint_logic(
            challenge_slug=request.challenge_slug,
            user_code=request.user_code,
            hint_level=request.hint_level,
            user_xp=request.user_xp,
            challenge_context=context_data,
        )
        return {"hint": safe_hint, "hint_level": request.hint_level, "max_hints": 3}
    except Exception:
        raise HTTPException(status_code=500, detail="Error generating hint")


@router.post("/analyze")
async def analyze_code(
    request: AnalyzeRequest,
    http_request: Request,
    x_internal_api_key: Optional[str] = Header(None, alias="X-Internal-API-Key"),
    x_internal_timestamp: Optional[str] = Header(None, alias="X-Internal-Timestamp"),
    x_internal_signature: Optional[str] = Header(None, alias="X-Internal-Signature"),
):
    if not authorize_internal_request(
        path=http_request.url.path,
        api_key=x_internal_api_key,
        timestamp=x_internal_timestamp,
        signature=x_internal_signature,
    ):
        raise HTTPException(status_code=403, detail="Unauthorized")

    if not settings.GROQ_API_KEY:
        raise HTTPException(status_code=500, detail="LLM API Key not configured")

    context_data = await fetch_challenge_context(request.challenge_slug)

    try:
        safe_review = await analyze_code_logic(
            challenge_slug=request.challenge_slug,
            user_code=request.user_code,
            challenge_context=context_data,
        )
        return {"review": safe_review}
    except Exception:
        raise HTTPException(status_code=500, detail="Error generating analysis")
