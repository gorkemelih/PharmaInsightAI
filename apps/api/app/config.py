"""Application configuration using Pydantic Settings."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # Database
    database_url: str = "postgresql://postgres:postgres@localhost:5432/pharmainsight"

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # CORS
    cors_origins: str = "http://localhost:3000"

    # API
    api_host: str = "0.0.0.0"
    api_port: int = 8000

    # LLM
    google_api_key: str = ""
    llm_model: str = "gemini-3-flash"
    llm_provider: str = "gemini"

    # Environment
    environment: str = "development"

    # JWT Settings
    jwt_secret: str = "super-secret-key-change-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60

    # Cookie Settings
    cookie_name: str = "pharmainsight_token"
    cookie_secure: bool = False  # Set True in production with HTTPS
    cookie_httponly: bool = True
    cookie_samesite: str = "lax"

    # Admin Seed
    admin_email: str = "admin@pharmainsight.io"
    admin_password: str = "changeme123"
    tenant_name: str = "Default Tenant"

    @property
    def cors_origins_list(self) -> list[str]:
        """Parse CORS origins as a list."""
        return [origin.strip() for origin in self.cors_origins.split(",")]

    @property
    def is_production(self) -> bool:
        """Check if running in production."""
        return self.environment == "production"


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
