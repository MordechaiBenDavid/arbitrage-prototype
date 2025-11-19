from functools import lru_cache
from typing import List, Optional, Union

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

    fedex_client_id: Optional[str] = None
    fedex_client_secret: Optional[str] = None
    fedex_base_url: str = "https://apis.fedex.com"

    ups_client_id: Optional[str] = None
    ups_client_secret: Optional[str] = None
    ups_base_url: str = "https://onlinetools.ups.com"

    usps_user_id: Optional[str] = None
    usps_base_url: str = "https://secure.shippingapis.com/ShippingAPI.dll"

    upcitemdb_api_key: Optional[str] = None
    upcitemdb_base_url: str = "https://api.upcitemdb.com"

    barcode_lookup_api_key: Optional[str] = None
    barcode_lookup_base_url: str = "https://api.barcodelookup.com/v3"

    access_token_expire_minutes: int = 60 * 24
    jwt_secret_key: str = "CHANGE_ME"
    jwt_algorithm: str = "HS256"

    cors_origins: Union[List[str], str] = ["*"]

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors(cls, value: Union[List[str], str]):
        if isinstance(value, str):
            return [origin.strip() for origin in value.split(",") if origin.strip()]
        return value


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
