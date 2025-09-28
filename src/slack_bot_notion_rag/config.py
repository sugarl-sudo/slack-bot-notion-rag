"""Configuration models and helpers for the Slack bot."""

from __future__ import annotations

from functools import lru_cache
from typing import List

from pydantic import BaseSettings, Field, validator


class Settings(BaseSettings):
    """Runtime configuration resolved from environment variables."""

    slack_signing_secret: str = Field(..., env="SLACK_SIGNING_SECRET")
    slack_bot_token: str = Field(..., env="SLACK_BOT_TOKEN")
    slack_app_token: str | None = Field(default=None, env="SLACK_APP_TOKEN")

    notion_api_token: str = Field(..., env="NOTION_API_TOKEN")
    notion_database_ids: List[str] = Field(default_factory=list, env="NOTION_DATABASE_IDS")

    openai_api_key: str = Field(..., env="OPENAI_API_KEY")
    openai_model: str = Field(default="gpt-4o-mini", env="OPENAI_MODEL")

    vector_store_path: str = Field(default="vector_store", env="VECTOR_STORE_PATH")
    embedding_model: str = Field(default="text-embedding-3-large", env="EMBEDDING_MODEL")

    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    answer_max_tokens: int = Field(default=800, env="ANSWER_MAX_TOKENS")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False

    @validator("notion_database_ids", pre=True)
    def _split_ids(cls, value: str | List[str]) -> List[str]:  # noqa: D401
        """Split comma-separated database identifiers."""

        if isinstance(value, list):
            return value
        if not value:
            return []
        return [item.strip() for item in value.split(",") if item.strip()]


@lru_cache
def get_settings() -> Settings:
    """Return cached configuration values."""

    return Settings()  # type: ignore[arg-type]
