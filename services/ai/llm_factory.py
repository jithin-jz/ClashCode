import logging

from config import settings
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_openai import ChatOpenAI

logger = logging.getLogger(__name__)


class LLMFactory:
    @staticmethod
    def get_llm() -> BaseChatModel:
        """
        Returns the configured Groq LLM instance.
        """
        if not settings.GROQ_API_KEY:
            logger.error("Groq API Key missing.")
            raise ValueError("Groq API Key must be set.")

        # logger.info("Initializing Groq LLM")
        return ChatOpenAI(
            api_key=settings.GROQ_API_KEY,
            base_url=settings.OPENAI_API_BASE,
            model=settings.MODEL_NAME,  # 'llama-3.3-70b-versatile'
            temperature=0.7,
        )

    @staticmethod
    def get_fallback_llm() -> BaseChatModel:
        """
        No fallback available in Groq-only mode. Returns main LLM.
        """
        return LLMFactory.get_llm()
