import logging

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from llm_factory import LLMFactory
from prompts import (
    CODE_REVIEW_SYSTEM_PROMPT,
    CODE_REVIEW_USER_TEMPLATE,
    HINT_GENERATION_SYSTEM_PROMPT,
    HINT_GENERATION_USER_TEMPLATE,
)
from utils.sanitizer import sanitize_guidance_output

from core.rag import get_rag_context

logger = logging.getLogger(__name__)


async def generate_hint_logic(
    challenge_slug: str,
    user_code: str,
    hint_level: int,
    user_xp: int,
    challenge_context: dict,
):
    challenge_title = challenge_context.get("challenge_title", challenge_context.get("title", ""))
    challenge_description = challenge_context.get("challenge_description", challenge_context.get("description", ""))

    # RAG Context
    rag_context = await get_rag_context(
        challenge_description=challenge_description,
        user_code=user_code,
        challenge_slug=challenge_slug,
    )

    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", HINT_GENERATION_SYSTEM_PROMPT),
            ("user", HINT_GENERATION_USER_TEMPLATE),
        ]
    )

    try:
        # Try primary provider
        try:
            llm = LLMFactory.get_llm()
            chain = prompt | llm | StrOutputParser()
            hint = await chain.ainvoke(
                {
                    "challenge_title": challenge_title,
                    "challenge_description": challenge_description,
                    "user_code": user_code,
                    "hint_level": hint_level,
                    "user_xp": user_xp,
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
                    "user_code": user_code,
                    "hint_level": hint_level,
                    "user_xp": user_xp,
                    "rag_context": rag_context,
                }
            )

        return sanitize_guidance_output(hint, mode="hint")
    except Exception as e:
        logger.error(f"LLM Error in generate_hint_logic: {e}", exc_info=True)
        raise e


async def analyze_code_logic(challenge_slug: str, user_code: str, challenge_context: dict):
    challenge_title = challenge_context.get("challenge_title", challenge_context.get("title", ""))
    challenge_description = challenge_context.get("challenge_description", challenge_context.get("description", ""))
    initial_code = challenge_context.get("initial_code", "")
    test_code = challenge_context.get("test_code", "")

    rag_context = await get_rag_context(
        challenge_description=challenge_description,
        user_code=user_code,
        challenge_slug=challenge_slug,
    )

    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", CODE_REVIEW_SYSTEM_PROMPT),
            ("user", CODE_REVIEW_USER_TEMPLATE),
        ]
    )

    try:
        try:
            llm = LLMFactory.get_llm()
            chain = prompt | llm | StrOutputParser()
            review = await chain.ainvoke(
                {
                    "challenge_title": challenge_title,
                    "challenge_description": challenge_description,
                    "initial_code": initial_code,
                    "user_code": user_code,
                    "test_code": test_code,
                    "rag_context": rag_context,
                }
            )
        except Exception as e:
            logger.warning(f"Primary LLM failed on analyze: {e}. Attempting fallback...")
            llm = LLMFactory.get_fallback_llm()
            chain = prompt | llm | StrOutputParser()
            review = await chain.ainvoke(
                {
                    "challenge_title": challenge_title,
                    "challenge_description": challenge_description,
                    "initial_code": initial_code,
                    "user_code": user_code,
                    "test_code": test_code,
                    "rag_context": rag_context,
                }
            )

        return sanitize_guidance_output(review, mode="analyze")
    except Exception as e:
        logger.error(f"LLM Error in analyze_code_logic: {e}", exc_info=True)
        raise e
