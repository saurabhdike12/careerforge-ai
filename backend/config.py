"""
CareerForge AI — Configuration Module
Centralizes all IBM watsonx.ai and application settings.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field
from functools import lru_cache


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # IBM watsonx.ai credentials (key is used by the underlying AI service)
    watsonx_api_key: str = Field(default="placeholder", alias="WATSONX_API_KEY")
    watsonx_url: str = Field(
        default="https://us-south.ml.cloud.ibm.com",
        alias="WATSONX_URL",
    )

    # IBM Granite Models
    granite_model_id: str = Field(
        default="ibm/granite-13b-chat-v2",
        alias="GRANITE_MODEL_ID",
    )
    granite_embedding_model: str = Field(
        default="ibm/slate-125m-english-rtrvr",
        alias="GRANITE_EMBEDDING_MODEL",
    )

    # Generation Parameters
    max_new_tokens: int = 1024
    temperature: float = 0.7
    top_p: float = 0.9
    repetition_penalty: float = 1.1

    # Application
    app_host: str = Field(default="0.0.0.0", alias="APP_HOST")
    app_port: int = Field(default=8000, alias="APP_PORT")
    debug: bool = Field(default=False, alias="DEBUG")
    secret_key: str = Field(default="changeme", alias="SECRET_KEY")

    # Database
    database_url: str = Field(
        default="sqlite:///./careerforge.db",
        alias="DATABASE_URL",
    )

    # Vector Store
    chroma_persist_dir: str = Field(
        default="./backend/data/chroma_db",
        alias="CHROMA_PERSIST_DIR",
    )

    # Session
    session_expiry_hours: int = Field(default=24, alias="SESSION_EXPIRY_HOURS")
    max_questions_per_session: int = Field(default=20, alias="MAX_QUESTIONS_PER_SESSION")

    # Rate Limiting
    max_requests_per_minute: int = Field(default=30, alias="MAX_REQUESTS_PER_MINUTE")


@lru_cache()
def get_settings() -> Settings:
    """Cached settings singleton — call this everywhere instead of instantiating Settings()."""
    return Settings()
