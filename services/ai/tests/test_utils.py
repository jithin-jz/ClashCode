from utils.sanitizer import sanitize_guidance_output


def test_sanitize_hint_removes_code_blocks():
    text = "Here is a hint: ```python\nprint('secret')\n```. You should try using a for loop."
    sanitized = sanitize_guidance_output(text, mode="hint")
    assert "print('secret')" not in sanitized
    assert "You should try using a for loop." in sanitized


def test_sanitize_hint_removes_code_lines():
    text = "Try this logic:\ndef my_func():\n    return True\nThat should work."
    sanitized = sanitize_guidance_output(text, mode="hint")
    assert "def my_func():" not in sanitized
    assert "return True" not in sanitized
    assert "That should work." in sanitized


def test_sanitize_empty_result_returns_fallback_hint():
    text = "```\nprint('only code')\n```"
    sanitized = sanitize_guidance_output(text, mode="hint")
    assert "Focus on the core logic" in sanitized


def test_sanitize_empty_result_returns_fallback_analyze():
    text = "def leak():\n    return True"  # Both are code-like
    sanitized = sanitize_guidance_output(text, mode="analyze")
    assert "Findings" in sanitized
    assert "Improve correctness" in sanitized
