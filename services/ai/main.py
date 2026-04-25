import logging
import re
import time
import hmac
from hashlib import sha256
from typing import Optional
import httpx
import asyncio

from fastapi import FastAPI, HTTPException, Header, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from dotenv import load_dotenv

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_community.embeddings import HuggingFaceInferenceAPIEmbeddings

# Local imports
from config import settings
from prompts import (
    HINT_GENERATION_SYSTEM_PROMPT,
    HINT_GENERATION_USER_TEMPLATE,
    CODE_REVIEW_SYSTEM_PROMPT,
    CODE_REVIEW_USER_TEMPLATE,
)

# Configure Logging
from logger_config import setup_logging
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration

# Sentry Configuration
if settings.SENTRY_DSN:
    sentry_sdk.init(
        dsn=settings.SENTRY_DSN,
        integrations=[FastApiIntegration()],
        # Performance Monitoring
        traces_sample_rate=1.0 if settings.DEBUG else 0.2,
        # Capture User PII
        send_default_pii=True,
        environment=settings.ENVIRONMENT,
    )

setup_logging()
logger = logging.getLogger(__name__)


load_dotenv()

# Initialize App
app = FastAPI(title="AI Service", version="1.0")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Global Exception Handler
@app.exception_handler(Exception)
async def global_exception_handler(request, exc: Exception):
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})


# Initialize RAG Components
# Using local embedding model to save API costs
_vector_db = None


def get_vector_db():
    """Lazy initialization of the vector database to handle connection issues gracefully."""
    global _vector_db
    if _vector_db is None:
        try:
            logger.info("Initializing Chroma RAG components...")
            embeddings = HuggingFaceInferenceAPIEmbeddings(
                api_key=settings.HUGGINGFACE_API_KEY,
                model_name=settings.EMBEDDING_MODEL,
            )
            # Connect to stand-alone ChromaDB server
            import chromadb

            _vector_db = Chroma(
                client=chromadb.HttpClient(
                    host=settings.CHROMA_SERVER_HOST,
                    port=settings.CHROMA_SERVER_HTTP_PORT,
                ),
                embedding_function=embeddings,
                collection_name="challenges",
            )
            logger.info("Chroma RAG components initialized successfully.")
        except Exception as e:
            logger.error(f"Failed to initialize Chroma RAG: {e}")
            _vector_db = None
    return _vector_db


# --- Models ---
class HintRequest(BaseModel):
    user_code: str
    challenge_slug: str
    language: str = "python"
    hint_level: int = Field(default=1, ge=1, le=3)  # 1: Vague, 2: Moderate, 3: Specific
    user_xp: int = 0


class AnalyzeRequest(BaseModel):
    user_code: str
    challenge_slug: str
    language: str = "python"


CODE_BLOCK_PATTERN = re.compile(r"```[\s\S]*?```", flags=re.MULTILINE)
CODE_LIKE_LINE_PATTERN = re.compile(
    r"^\s*(def |class |for |while |if |elif |else:|try:|except |return |import |from |\w+\s*=|print\(|\w+\(.*\):)"
)


def sanitize_guidance_output(text: str, mode: str) -> str:
    """
    Removes code-like answer leakage from model output so only guidance remains.
    """
    if not text:
        return text

    without_blocks = CODE_BLOCK_PATTERN.sub("", text)
    kept_lines = []
    removed_code_lines = 0

    for line in without_blocks.splitlines():
        if CODE_LIKE_LINE_PATTERN.match(line):
            removed_code_lines += 1
            continue
        kept_lines.append(line)

    cleaned = "\n".join(kept_lines).strip()

    if removed_code_lines:
        logger.warning(
            "Sanitized %s code-like lines from %s response.", removed_code_lines, mode
        )

    if cleaned:
        return cleaned

    if mode == "hint":
        return (
            "Focus on the core logic, break the problem into small steps, "
            "and implement each step without copying a full solution."
        )

    return (
        "Findings\n"
        "- Improve correctness by validating edge cases first.\n\n"
        "Edge Cases\n"
        "- Test empty input, minimal input, and boundary values.\n\n"
        "Complexity\n"
        "- Re-evaluate time and space complexity for your current approach.\n\n"
        "Refactor Suggestion\n"
        "- Split logic into small functions with clear responsibilities."
    )


def _build_internal_headers(path: str) -> dict[str, str]:
    headers = {"X-Internal-API-Key": settings.INTERNAL_API_KEY}
    signing_secret = (settings.INTERNAL_SIGNING_SECRET or "").strip()
    if signing_secret:
        timestamp = str(int(time.time()))
        signature = hmac.new(
            signing_secret.encode("utf-8"),
            f"{timestamp}:{path}".encode("utf-8"),
            sha256,
        ).hexdigest()
        headers["X-Internal-Timestamp"] = timestamp
        headers["X-Internal-Signature"] = signature
    return headers


def _authorize_internal_request(
    path: str,
    api_key: Optional[str],
    timestamp: Optional[str],
    signature: Optional[str],
) -> bool:
    if api_key != settings.INTERNAL_API_KEY:
        return False

    signing_secret = (settings.INTERNAL_SIGNING_SECRET or "").strip()
    if not signing_secret:
        return not settings.INTERNAL_REQUIRE_SIGNATURE

    if not timestamp or not signature:
        return False
    try:
        ts = int(timestamp)
    except (TypeError, ValueError):
        return False

    if abs(int(time.time()) - ts) > 120:
        return False

    expected = hmac.new(
        signing_secret.encode("utf-8"),
        f"{timestamp}:{path}".encode("utf-8"),
        sha256,
    ).hexdigest()
    return hmac.compare_digest(expected, signature)


async def fetch_challenge_context(challenge_slug: str):
    try:
        path = f"/api/challenges/{challenge_slug}/context/"
        url = f"{settings.CORE_SERVICE_URL}{path}"
        headers = _build_internal_headers(path)
        logger.info(f"Fetching context from: {url}")
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers, timeout=5)
            if response.status_code != 200:
                logger.error(
                    f"Core service error: {response.status_code} - {response.text}"
                )
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"Core service returned {response.status_code}",
                )
            return response.json()
    except httpx.RequestError as e:
        logger.error(f"Error connecting to Core Service: {e}")
        raise HTTPException(status_code=503, detail="Core service unavailable")


async def get_rag_context(
    challenge_description: str, user_code: str, challenge_slug: str
):
    logger.info("Performing similarity search for RAG...")
    similar_docs = []
    try:
        query = f"Challenge: {challenge_description}\n\nUser Code: {user_code}"

        vdb = get_vector_db()
        if vdb is None:
            logger.warning("Vector DB not available for similarity search.")
            return "No similar patterns found."

        loop = asyncio.get_running_loop()
        results = await loop.run_in_executor(
            None, lambda: vdb.similarity_search(query, k=2)
        )
        similar_docs = [
            doc.page_content
            for doc in results
            if doc.metadata.get("slug") != challenge_slug
        ]
    except Exception as e:
        logger.warning(f"RAG Search failed: {e}. Proceeding without extra context.")
    return "\n\n".join(similar_docs) if similar_docs else "No similar patterns found."


@app.post("/index")
async def index_challenges(
    http_request: Request,
    x_internal_api_key: Optional[str] = Header(None, alias="X-Internal-API-Key"),
    x_internal_timestamp: Optional[str] = Header(None, alias="X-Internal-Timestamp"),
    x_internal_signature: Optional[str] = Header(None, alias="X-Internal-Signature"),
):
    """
    Internal endpoint to trigger re-indexing of all challenges from Core.
    This ensures the RAG context is up-to-date and "pre-warmed".
    """
    if not _authorize_internal_request(
        path=http_request.url.path,
        api_key=x_internal_api_key,
        timestamp=x_internal_timestamp,
        signature=x_internal_signature,
    ):
        raise HTTPException(status_code=403, detail="Unauthorized")

    logger.info("Starting challenge indexing (RAG pre-warming)...")

    # 1. Fetch all challenges from Core
    path = "/api/challenges/internal-list/"
    url = f"{settings.CORE_SERVICE_URL}{path}"
    headers = _build_internal_headers(path)

    async with httpx.AsyncClient() as client:
        try:
            resp = await client.get(url, headers=headers, timeout=10)
            if resp.status_code != 200:
                logger.error(f"Failed to fetch challenges for indexing: {resp.text}")
                return {"status": "error", "detail": "Core service fetch failed"}
            challenges = resp.json()
        except Exception as e:
            logger.error(f"Error connecting to Core for indexing: {e}")
            return {"status": "error", "detail": str(e)}

    # 2. Initialize Vector DB
    vdb = get_vector_db()
    if vdb is None:
        return {"status": "error", "detail": "Vector DB initialization failed"}

    # 3. Create LangChain Documents
    docs = []
    for c in challenges:
        content = (
            f"Title: {c.get('title')}\n"
            f"Description: {c.get('description')}\n"
            f"Initial Code:\n{c.get('initial_code')}\n"
        )
        docs.append(
            Document(
                page_content=content,
                metadata={"slug": c.get("slug"), "type": "challenge_context"},
            )
        )

    # 4. Add to Vector DB (runs in background thread to avoid blocking)
    try:
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(None, lambda: vdb.add_documents(docs))
        logger.info(f"Successfully indexed {len(docs)} challenges.")
        return {"status": "ok", "indexed_count": len(docs)}
    except Exception as e:
        logger.error(f"Failed to add documents to Chroma: {e}")
        return {"status": "error", "detail": "Chroma storage failed"}


# --- Routes ---


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/hints")
async def generate_hint(
    request: HintRequest,
    http_request: Request,
    x_internal_api_key: Optional[str] = Header(None, alias="X-Internal-API-Key"),
    x_internal_timestamp: Optional[str] = Header(None, alias="X-Internal-Timestamp"),
    x_internal_signature: Optional[str] = Header(None, alias="X-Internal-Signature"),
):
    logger.info(f"Received hint request for challenge: {request.challenge_slug}")

    if not _authorize_internal_request(
        path=http_request.url.path,
        api_key=x_internal_api_key,
        timestamp=x_internal_timestamp,
        signature=x_internal_signature,
    ):
        logger.warning(f"Unauthorized hint request. Key: {x_internal_api_key}")
        raise HTTPException(status_code=403, detail="Unauthorized")

    if not settings.GROQ_API_KEY:
        logger.error("No LLM API Keys configured")
        raise HTTPException(status_code=500, detail="LLM API Key not configured")

    # 1. Fetch Challenge Context from Core Service
    context_data = await fetch_challenge_context(request.challenge_slug)

    # 2. Extract Data
    challenge_title = context_data.get("challenge_title", context_data.get("title", ""))
    challenge_description = context_data.get(
        "challenge_description", context_data.get("description", "")
    )

    # 3. RAG: Search for similar challenges
    rag_context = await get_rag_context(
        challenge_description=challenge_description,
        user_code=request.user_code,
        challenge_slug=request.challenge_slug,
    )

    # 4. Construct Prompt
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", HINT_GENERATION_SYSTEM_PROMPT),
            ("user", HINT_GENERATION_USER_TEMPLATE),
        ]
    )

    # 5. Call LLM
    try:
        logger.info(f"Initializing LLM via Factory (Provider: {settings.LLM_PROVIDER})")
        from llm_factory import LLMFactory

        # Try primary provider
        try:
            llm = LLMFactory.get_llm()
            chain = prompt | llm | StrOutputParser()
            hint = await chain.ainvoke(
                {
                    "challenge_title": challenge_title,
                    "challenge_description": challenge_description,
                    "user_code": request.user_code,
                    "hint_level": request.hint_level,
                    "user_xp": request.user_xp,
                    "rag_context": rag_context,
                }
            )
        except Exception as e:
            logger.warning(f"Primary LLM failed: {e}. Attempting fallback...")
            llm = LLMFactory.get_fallback_llm()
            chain = prompt | llm | StrOutputParser()
            hint = await chain.ainvoke(
                {
                    "challenge_title": challenge_title,
                    "challenge_description": challenge_description,
                    "user_code": request.user_code,
                    "hint_level": request.hint_level,
                    "user_xp": request.user_xp,
                    "rag_context": rag_context,
                }
            )

        safe_hint = sanitize_guidance_output(hint, mode="hint")
        logger.info("Hint generated successfully")
        return {"hint": safe_hint, "hint_level": request.hint_level, "max_hints": 3}
    except Exception as e:
        logger.error(f"LLM Error (All providers failed): {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Error generating hint")


@app.post("/analyze")
async def analyze_code(
    request: AnalyzeRequest,
    http_request: Request,
    x_internal_api_key: Optional[str] = Header(None, alias="X-Internal-API-Key"),
    x_internal_timestamp: Optional[str] = Header(None, alias="X-Internal-Timestamp"),
    x_internal_signature: Optional[str] = Header(None, alias="X-Internal-Signature"),
):
    logger.info(f"Received analyze request for challenge: {request.challenge_slug}")

    if not _authorize_internal_request(
        path=http_request.url.path,
        api_key=x_internal_api_key,
        timestamp=x_internal_timestamp,
        signature=x_internal_signature,
    ):
        logger.warning(f"Unauthorized analyze request. Key: {x_internal_api_key}")
        raise HTTPException(status_code=403, detail="Unauthorized")

    if not settings.GROQ_API_KEY:
        logger.error("No LLM API Keys configured")
        raise HTTPException(status_code=500, detail="LLM API Key not configured")

    context_data = await fetch_challenge_context(request.challenge_slug)
    challenge_title = context_data.get("challenge_title", context_data.get("title", ""))
    challenge_description = context_data.get(
        "challenge_description", context_data.get("description", "")
    )
    initial_code = context_data.get("initial_code", "")
    test_code = context_data.get("test_code", "")
    rag_context = await get_rag_context(
        challenge_description=challenge_description,
        user_code=request.user_code,
        challenge_slug=request.challenge_slug,
    )

    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", CODE_REVIEW_SYSTEM_PROMPT),
            ("user", CODE_REVIEW_USER_TEMPLATE),
        ]
    )

    try:
        from llm_factory import LLMFactory

        try:
            llm = LLMFactory.get_llm()
            chain = prompt | llm | StrOutputParser()
            review = await chain.ainvoke(
                {
                    "challenge_title": challenge_title,
                    "challenge_description": challenge_description,
                    "initial_code": initial_code,
                    "user_code": request.user_code,
                    "test_code": test_code,
                    "rag_context": rag_context,
                }
            )
        except Exception as e:
            logger.warning(
                f"Primary LLM failed on analyze: {e}. Attempting fallback..."
            )
            llm = LLMFactory.get_fallback_llm()
            chain = prompt | llm | StrOutputParser()
            review = await chain.ainvoke(
                {
                    "challenge_title": challenge_title,
                    "challenge_description": challenge_description,
                    "initial_code": initial_code,
                    "user_code": request.user_code,
                    "test_code": test_code,
                    "rag_context": rag_context,
                }
            )

        safe_review = sanitize_guidance_output(review, mode="analyze")
        logger.info("AI code review generated successfully")
        return {"review": safe_review}
    except Exception as e:
        logger.error(f"LLM Error on analyze (All providers failed): {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Error generating analysis")
