"""Agentic coding tutor built on LangGraph.

Instead of a single stateless LLM call, this runs a reason-act loop: the model
can execute the learner's code in the sandbox and search the knowledge base,
observe the real results, and only then produce an adaptive hint. The current
single-shot chain in ``ai_logic`` remains available as a fallback.
"""

import logging
from typing import Annotated, TypedDict

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode
from llm_factory import LLMFactory
from prompts import AGENT_SYSTEM_PROMPT, AGENT_TASK_TEMPLATE

from core.agent_tools import build_tools
from utils.core_client import fetch_challenge_context

logger = logging.getLogger(__name__)

# Safety cap on the reason-act loop so a misbehaving model cannot spin forever.
_MAX_ITERATIONS = 6


class TutorState(TypedDict):
    """Conversation state threaded through the graph."""

    messages: Annotated[list[BaseMessage], add_messages]


def _build_graph(tools):
    """Compile a reason-act StateGraph bound to the given tools."""
    llm_with_tools = LLMFactory.get_llm().bind_tools(tools)
    tool_node = ToolNode(tools)

    async def agent_node(state: TutorState) -> dict:
        response = await llm_with_tools.ainvoke(state["messages"])
        return {"messages": [response]}

    def route(state: TutorState) -> str:
        last = state["messages"][-1]
        if isinstance(last, AIMessage) and last.tool_calls:
            return "tools"
        return END

    graph = StateGraph(TutorState)
    graph.add_node("agent", agent_node)
    graph.add_node("tools", tool_node)
    graph.add_edge(START, "agent")
    graph.add_conditional_edges("agent", route, {"tools": "tools", END: END})
    graph.add_edge("tools", "agent")
    return graph.compile()


def _summarize_tool_trace(messages: list[BaseMessage]) -> list[str]:
    """Extract a human-readable list of the tools the agent invoked."""
    trace: list[str] = []
    for msg in messages:
        if isinstance(msg, AIMessage) and msg.tool_calls:
            for call in msg.tool_calls:
                trace.append(call.get("name", "unknown_tool"))
    return trace


async def run_agent_hint(
    *,
    challenge_slug: str,
    user_code: str,
    hint_level: int,
    user_xp: int,
    challenge_context: dict | None = None,
) -> dict:
    """Run the agentic tutor and return the final hint plus a tool trace.

    Returns ``{"hint": str, "tool_trace": list[str]}``.
    """
    context = challenge_context or await fetch_challenge_context(challenge_slug)
    challenge_title = context.get("challenge_title", context.get("title", ""))
    challenge_description = context.get(
        "challenge_description", context.get("description", "")
    )
    test_code = context.get("test_code", "")

    tools = build_tools(
        challenge_slug=challenge_slug,
        challenge_description=challenge_description,
        user_code=user_code,
        test_code=test_code,
    )
    app = _build_graph(tools)

    task = AGENT_TASK_TEMPLATE.format(
        challenge_title=challenge_title,
        challenge_description=challenge_description,
        user_code=user_code,
        hint_level=hint_level,
        user_xp=user_xp,
    )
    initial_state: TutorState = {
        "messages": [
            SystemMessage(content=AGENT_SYSTEM_PROMPT),
            HumanMessage(content=task),
        ]
    }

    result = await app.ainvoke(initial_state, config={"recursion_limit": _MAX_ITERATIONS * 2})

    final_message = result["messages"][-1]
    hint = final_message.content if isinstance(final_message, AIMessage) else str(final_message)
    trace = _summarize_tool_trace(result["messages"])
    logger.info("Agent tutor completed. Tools used: %s", trace or "none")

    return {"hint": hint, "tool_trace": trace}
