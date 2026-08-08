"""Tools exposed to the agentic tutor.

Tools are built per-request via :func:`build_tools` so that the learner's code,
the hidden test code, and the challenge slug are captured in closures. The LLM
therefore never has to pass large/opaque payloads as tool arguments — it just
decides *when* to run the code or search for related material.
"""

import logging

from langchain_core.tools import StructuredTool

from core.rag import get_rag_context
from utils.executor_client import run_code_in_sandbox

logger = logging.getLogger(__name__)


def build_tools(
    *,
    challenge_slug: str,
    challenge_description: str,
    user_code: str,
    test_code: str,
) -> list[StructuredTool]:
    """Construct the tool set for a single tutoring request."""

    async def run_challenge_tests() -> str:
        """Run the learner's current code against the hidden challenge tests in a
        secure sandbox. Use this to find out what is actually failing before giving
        a hint. Returns whether the tests passed and any error output."""
        if not test_code:
            return "No hidden tests are available for this challenge."

        full_code = f"{user_code}\n\n{test_code}"
        result = await run_code_in_sandbox(full_code)

        if not result["ok"]:
            return f"Could not run the tests: {result['stderr']}"

        passed = result["exit_code"] == 0 and not result["stderr"].strip()
        if passed:
            return "All tests PASSED. The solution is correct."

        parts = ["Tests FAILED."]
        if result["stderr"]:
            parts.append(f"Error output:\n{result['stderr']}")
        if result["stdout"]:
            parts.append(f"Standard output:\n{result['stdout']}")
        parts.append(f"Exit code: {result['exit_code']}")
        return "\n\n".join(parts)

    async def search_similar_challenges(query: str = "") -> str:
        """Search the knowledge base for related challenges and coding patterns.
        Provide a focused natural-language query describing the concept you want
        context on (e.g. 'two pointer technique for sorted arrays'). Leave empty
        to use the current challenge description."""
        effective_query = query.strip() or challenge_description
        return await get_rag_context(
            challenge_description=effective_query,
            user_code=user_code,
            challenge_slug=challenge_slug,
        )

    return [
        StructuredTool.from_function(
            coroutine=run_challenge_tests,
            name="run_challenge_tests",
            description=run_challenge_tests.__doc__,
        ),
        StructuredTool.from_function(
            coroutine=search_similar_challenges,
            name="search_similar_challenges",
            description=search_similar_challenges.__doc__,
        ),
    ]
