import asyncio
import logging

from config import settings
from langchain_pinecone import PineconeEmbeddings, PineconeVectorStore

logger = logging.getLogger(__name__)

_vector_db = None


def get_vector_db():
    """Lazy initialization of the vector database to handle connection issues gracefully."""
    global _vector_db
    if _vector_db is None:
        try:
            logger.info("Initializing Pinecone RAG components with native embeddings...")

            # Using Pinecone's native embedding model (matching your 1024-dim index)
            embeddings = PineconeEmbeddings(model=settings.EMBEDDING_MODEL, pinecone_api_key=settings.PINECONE_API_KEY)

            _vector_db = PineconeVectorStore(
                index_name=settings.PINECONE_INDEX_NAME,
                embedding=embeddings,
                pinecone_api_key=settings.PINECONE_API_KEY,
            )
            logger.info("Pinecone RAG components initialized successfully.")
        except Exception as e:
            logger.error(f"Failed to initialize Pinecone RAG: {e}")
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
