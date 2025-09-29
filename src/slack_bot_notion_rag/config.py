"""Configuration models and helpers for the Slack bot."""

from __future__ import annotations

from functools import lru_cache
from typing import List

from pydantic import Field, validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Runtime configuration resolved from environment variables."""

    slack_signing_secret: str = Field(..., env="SLACK_SIGNING_SECRET")
    slack_bot_token: str = Field(..., env="SLACK_BOT_TOKEN")
    slack_app_token: str | None = Field(default=None, env="SLACK_APP_TOKEN")

    notion_api_token: str = Field(..., env="NOTION_API_TOKEN")
    notion_root_page_ids: List[str] = Field(default_factory=list, env="NOTION_ROOT_PAGE_IDS")
    notion_page_size: int = Field(default=50, env="NOTION_PAGE_SIZE")
    notion_request_timeout: float = Field(default=30.0, env="NOTION_REQUEST_TIMEOUT")

    openai_api_key: str = Field(..., env="OPENAI_API_KEY")
    openai_model: str = Field(default="gpt-4o-mini", env="OPENAI_MODEL")
    openai_temperature: float = Field(default=0.2, env="OPENAI_TEMPERATURE")
    openai_api_base: str | None = Field(default=None, env="OPENAI_API_BASE")

    vector_store_path: str = Field(default="vector_store", env="VECTOR_STORE_PATH")
    vector_collection_name: str = Field(default="notion-knowledge", env="VECTOR_COLLECTION_NAME")
    embedding_model: str = Field(default="text-embedding-3-large", env="EMBEDDING_MODEL")

    chunk_size: int = Field(default=800, env="CHUNK_SIZE")
    chunk_overlap: int = Field(default=200, env="CHUNK_OVERLAP")
    retriever_top_k: int = Field(default=4, env="RETRIEVER_TOP_K")

    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    answer_max_tokens: int = Field(default=800, env="ANSWER_MAX_TOKENS")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False

    @validator("notion_root_page_ids", pre=True)
    def _split_ids(cls, value: str | List[str]) -> List[str]:  # noqa: D401
        """Split comma-separated Notion identifiers."""

        if isinstance(value, list):
            return value
        if not value:
            return []
        return [item.strip() for item in value.split(",") if item.strip()]

    @validator("notion_page_size")
    def _validate_page_size(cls, value: int) -> int:
        if value <= 0 or value > 100:
            raise ValueError("NOTION_PAGE_SIZE must be between 1 and 100")
        return value

    @validator("chunk_size")
    def _validate_chunk_size(cls, value: int) -> int:
        if value <= 0:
            raise ValueError("CHUNK_SIZE must be positive")
        return value

    @validator("chunk_overlap")
    def _validate_chunk_overlap(cls, value: int, values: dict[str, int]) -> int:
        chunk_size = values.get("chunk_size", 1)
        if value < 0 or value >= chunk_size:
            raise ValueError("CHUNK_OVERLAP must be >= 0 and smaller than CHUNK_SIZE")
        return value

    @validator("retriever_top_k")
    def _validate_retriever_top_k(cls, value: int) -> int:
        if value <= 0:
            raise ValueError("RETRIEVER_TOP_K must be positive")
        return value

    @validator("openai_temperature")
    def _validate_temperature(cls, value: float) -> float:
        if value < 0 or value > 1:
            raise ValueError("OPENAI_TEMPERATURE must be within [0, 1]")
        return value


@lru_cache
def get_settings() -> Settings:
    """Return cached configuration values."""

    return Settings()  # type: ignore[arg-type]
