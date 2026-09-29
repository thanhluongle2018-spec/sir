from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(".env", "../.env", "/workspace/.env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "日本二手商品监控"
    app_env: str = "development"
    secret_key: str = "change-me-in-production"
    # Fernet key used to encrypt channel credentials at rest (url-safe base64 32-byte key)
    credentials_fernet_key: str = ""

    database_url: str = "sqlite:////workspace/data/monitor.db"
    cors_origins: str = "http://localhost:5173,http://localhost:3000,http://127.0.0.1:5173"

    # Scheduler
    scheduler_enabled: bool = True
    default_check_interval_seconds: int = 60
    min_check_interval_seconds: int = 30
    max_concurrent_platform_requests: int = 3
    request_timeout_seconds: float = 20.0
    max_items_per_search: int = 30

    # Rate limiting / backoff
    platform_min_interval_seconds: float = 1.5
    retry_max_attempts: int = 3
    retry_base_seconds: float = 2.0

    # User-Agent for outbound HTTP (identify this open-source tool; do not impersonate browsers to bypass controls)
    http_user_agent: str = (
        "JP-Monitor/1.0 (+https://github.com/thanhluongle2018-spec/sir; personal monitoring)"
    )

    # Demo platform: generates synthetic items so the pipeline can be tested offline
    enable_demo_platform: bool = True

    static_dir: str = str(Path(__file__).resolve().parents[2] / "frontend" / "dist")

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
