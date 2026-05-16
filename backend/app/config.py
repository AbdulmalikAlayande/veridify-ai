import tempfile
from functools import lru_cache
from pathlib import Path

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


def _default_temp_dir() -> str:
    # Cross-platform default — Linux/Render → /tmp/veridify, Windows local dev → %TEMP%\veridify.
    return str(Path(tempfile.gettempdir()) / "veridify")


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=False,
        extra="ignore",
        protected_namespaces=("settings_",),
    )

    app_env: str = "development"
    app_name: str = "Veridifi"
    secret_key: str

    database_url: str
    squad_secret_key: str = ""
    squad_base_url: str = "https://sandbox-api-d.squadco.com"
    squad_webhook_secret: str = ""
    squad_currency: str = "NGN"
    # Sandbox-friendly defaults — GTBank settlement account + test BVN/mobile
    # supplied to Squad's B2B virtual-account endpoint. Override in .env for prod.
    squad_beneficiary_account: str = "0123456789"
    squad_test_bvn: str = "12345678901"
    squad_test_mobile: str = "08000000000"

    model_path: str = "./models/dual_branch_v1.keras"
    mock_inference: bool = True

    verification_cost_naira: int = 175
    rate_limit_per_minute: int = 60
    max_image_size_mb: int = 10
    temp_file_dir: str = _default_temp_dir()
    image_retention_seconds: int = 60
    cache_ttl_hours: int = 24

    allowed_origins: str = "http://localhost:5173"

    @field_validator("database_url", mode="before")
    @classmethod
    def _coerce_async_driver(cls, v: str) -> str:
        # Render emits `postgres://`, Heroku/older Render emit `postgresql://`.
        # SQLAlchemy 2.x rejects `postgres://` entirely and needs the asyncpg driver.
        if isinstance(v, str):
            if v.startswith("postgres://"):
                return "postgresql+asyncpg://" + v[len("postgres://"):]
            if v.startswith("postgresql://"):
                return "postgresql+asyncpg://" + v[len("postgresql://"):]
        return v


@lru_cache()
def get_settings() -> Settings:
    return Settings()
