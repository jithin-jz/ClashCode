from pydantic import BaseModel, Field


class TestCase(BaseModel):
    """A single test case with input and expected output."""

    input: str = ""
    expected_output: str | None = None


class ExecuteRequest(BaseModel):
    language: str = "python"
    code: str = Field(default="", max_length=1024 * 1024)
    stdin: str = ""
    runner: str = "host"  # "host" or "docker"
    test_cases: list[TestCase] | None = None  # Batch test cases
