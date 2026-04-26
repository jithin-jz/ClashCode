import logging
import re

logger = logging.getLogger(__name__)

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
        logger.warning("Sanitized %s code-like lines from %s response.", removed_code_lines, mode)

    if cleaned:
        return cleaned

    if mode == "hint":
        return "Focus on the core logic, break the problem into small steps, and implement each step without copying a full solution."

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
