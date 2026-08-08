from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Service URLs
    CORE_SERVICE_URL: str
    EXECUTOR_SERVICE_URL: str = "http://executor-service:8011"

    # API Keys & Auth
    # API Keys & Auth
    INTERNAL_API_KEY: str
    INTERNAL_SIGNING_SECRET: str | None = None
    INTERNAL_REQUIRE_SIGNATURE: bool = True
    GROQ_API_KEY: str | None = None
    HUGGINGFACE_API_KEY: str | None = None

    # LLM Settings
    LLM_PROVIDER: str = "groq"
    MODEL_NAME: str
    OPENAI_API_BASE: str

    # RAG Settings
    EMBEDDING_MODEL: str
    PINECONE_API_KEY: str
    PINECONE_INDEX_NAME: str

    # Security
    CORS_ORIGINS: str | list[str]

    # Observability
    SENTRY_DSN: str | None = Field(default=None, alias="SENTRY_DSN")
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
