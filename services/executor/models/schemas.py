from pydantic import BaseModel, Field


class ExecuteRequest(BaseModel):
    language: str = "python"
    code: str = Field(default="", max_length=1024 * 1024)
    stdin: str = ""
    runner: str = "host"  # "host" or "docker"
