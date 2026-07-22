from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Enterprise AI Knowledge Assistant"
    app_env: str = "development"
    app_debug: bool = True
    frontend_base_url: str = "http://127.0.0.1:5173"

    database_url: str = (
        "sqlite+aiosqlite:///./knowledge_assistant.db"
    )

    documents_storage_directory: Path = Path(
        "storage/documents"
    )

    chroma_storage_directory: Path = Path(
        "storage/chroma"
    )

    mail_outbox_directory: Path = Path(
        "storage/mail_outbox"
    )

    cors_origins: str = (
        "http://localhost:5173,"
        "http://127.0.0.1:5173,"
        "http://localhost:5174,"
        "http://127.0.0.1:5174,"
        "http://localhost:5175,"
        "http://127.0.0.1:5175"
    )

    jwt_secret_key: str = Field(
        default="change-this-secret-key-in-production",
        min_length=32,
    )

    jwt_algorithm: str = "HS256"

    access_token_expire_minutes: int = 15
    refresh_token_expire_days: int = 7
    account_action_token_expire_minutes: int = 30

    access_cookie_name: str = "knowledge_ai_access"
    refresh_cookie_name: str = "knowledge_ai_refresh"
    auth_cookie_domain: str | None = None
    auth_cookie_secure: bool = False
    auth_cookie_samesite: str = "auto"

    login_max_failed_attempts: int = 5
    login_lock_minutes: int = 15
    auth_rate_limit_requests: int = 20
    auth_rate_limit_window_seconds: int = 60

    mail_delivery_mode: str = "outbox"
    mail_from_address: str = "no-reply@knowledge-ai.local"
    smtp_host: str | None = None
    smtp_port: int = 587
    smtp_username: str | None = None
    smtp_password: str | None = None
    smtp_use_tls: bool = True

    @property
    def cors_origin_list(self) -> list[str]:
        return [
            origin.strip()
            for origin in self.cors_origins.split(",")
            if origin.strip()
        ]

    @property
    def effective_cookie_secure(self) -> bool:
        return self.auth_cookie_secure or self.app_env.lower() == "production"

    @property
    def effective_cookie_samesite(self) -> str:
        value = self.auth_cookie_samesite.lower().strip()
        if value == "auto":
            return "none" if self.effective_cookie_secure else "lax"
        if value not in {"lax", "strict", "none"}:
            return "none" if self.effective_cookie_secure else "lax"
        if value == "none" and not self.effective_cookie_secure:
            return "lax"
        return value

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
