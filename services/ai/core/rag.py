import asyncio
import logging

from config import settings
from langchain_chroma import Chroma
from langchain_community.embeddings import HuggingFaceInferenceAPIEmbeddings

logger = logging.getLogger(__name__)

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


async def get_rag_context(challenge_description: str, user_code: str, challenge_slug: str):
    logger.info("Performing similarity search for RAG...")
    similar_docs = []
    try:
        query = f"Challenge: {challenge_description}\n\nUser Code: {user_code}"

        vdb = get_vector_db()
        if vdb is None:
            logger.warning("Vector DB not available for similarity search.")
            return "No similar patterns found."

        loop = asyncio.get_running_loop()
        results = await loop.run_in_executor(None, lambda: vdb.similarity_search(query, k=2))
        similar_docs = [doc.page_content for doc in results if doc.metadata.get("slug") != challenge_slug]
    except Exception as e:
        logger.warning(f"RAG Search failed: {e}. Proceeding without extra context.")
    return "\n\n".join(similar_docs) if similar_docs else "No similar patterns found."
