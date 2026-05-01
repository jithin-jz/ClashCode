from typing import List, Optional, Union

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Service URLs
    CORE_SERVICE_URL: str

    # API Keys & Auth
    # API Keys & Auth
    INTERNAL_API_KEY: str
    INTERNAL_SIGNING_SECRET: Optional[str] = None
    INTERNAL_REQUIRE_SIGNATURE: bool = True
    GROQ_API_KEY: Optional[str] = None
    HUGGINGFACE_API_KEY: Optional[str] = None

    # LLM Settings
    LLM_PROVIDER: str = "groq"
    MODEL_NAME: str
    OPENAI_API_BASE: str

    # RAG Settings
    EMBEDDING_MODEL: str
    PINECONE_API_KEY: str
    PINECONE_INDEX_NAME: str

    # Security
    CORS_ORIGINS: Union[str, List[str]]

    # Observability
    SENTRY_DSN: Optional[str] = Field(default=None, alias="SENTRY_DSN")
    DEBUG: bool = Field(default=False)
    ENVIRONMENT: str = Field(default="production")

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @field_validator("CORS_ORIGINS", mode="before")
    def split_cors_origins(cls, v):
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v

    def validate_keys(self):
        if not self.INTERNAL_API_KEY or not self.INTERNAL_API_KEY.strip():
            raise ValueError("INTERNAL_API_KEY must be set and non-empty")
        if self.INTERNAL_REQUIRE_SIGNATURE and not (
            self.INTERNAL_SIGNING_SECRET and self.INTERNAL_SIGNING_SECRET.strip()
        ):
            raise ValueError("INTERNAL_SIGNING_SECRET must be set when INTERNAL_REQUIRE_SIGNATURE is true")


settings = Settings()
settings.validate_keys()
