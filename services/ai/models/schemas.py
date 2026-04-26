from pydantic import BaseModel, Field


class HintRequest(BaseModel):
    user_code: str
    challenge_slug: str
    language: str = "python"
    hint_level: int = Field(default=1, ge=1, le=3)  # 1: Vague, 2: Moderate, 3: Specific
    user_xp: int = 0


class AnalyzeRequest(BaseModel):
    user_code: str
    challenge_slug: str
    language: str = "python"
