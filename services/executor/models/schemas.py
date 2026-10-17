import os

from pydantic import BaseModel, Field

MAX_CODE_BYTES = int(os.getenv("EXECUTOR_MAX_CODE_BYTES", str(64 * 1024)))
MAX_STDIN_BYTES = 64 * 1024
MAX_TEST_CASES = 20


class TestCase(BaseModel):
    """A single test case with input and expected output."""

    input: str = Field(default="", max_length=MAX_STDIN_BYTES)
    expected_output: str | None = Field(default=None, max_length=MAX_STDIN_BYTES)


class ExecuteRequest(BaseModel):
    language: str = "python"
    code: str = Field(default="", max_length=MAX_CODE_BYTES)
    stdin: str = Field(default="", max_length=MAX_STDIN_BYTES)
    # Challenge assertions run by the trusted harness; the result carries "passed".
    test_code: str | None = Field(default=None, max_length=MAX_CODE_BYTES)
    # Batch stdin/stdout test cases.
    test_cases: list[TestCase] | None = Field(default=None, max_length=MAX_TEST_CASES)
