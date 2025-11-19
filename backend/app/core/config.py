from functools import lru_cache
from typing import List

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application configuration sourced from environment variables."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", case_sensitive=False)

    project_name: str = "SKU Lifecycle Tracker"
    api_v1_prefix: str = "/api/v1"

    database_url: str = "postgresql+psycopg://app:app@db:5432/sku_lifecycle"
    redis_url: str = "redis://redis:6379/0"
    opensearch_host: str = "http://opensearch:9200"

    access_token_expire_minutes: int = 60 * 24
    jwt_secret_key: str = "CHANGE_ME"
    jwt_algorithm: str = "HS256"

    cors_origins: List[str] = ["*"]

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors(cls, value: List[str] | str):
        if isinstance(value, str):
            return [origin.strip() for origin in value.split(",") if origin.strip()]
        return value


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
