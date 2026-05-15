from functools import lru_cache

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_env: str = "development"
    app_name: str = "Veridifi"
    secret_key: str

    database_url: str
    squad_secret_key: str
    squad_base_url: str = "https://sandbox-api-d.squadco.com"
    squad_webhook_secret: str

    model_path: str = "./models/dual_branch_v1.keras"
    mock_inference: bool = True

    verification_cost_naira: int = 175
    rate_limit_per_minute: int = 60
    max_image_size_mb: int = 10
    temp_file_dir: str = "/tmp/veridifi"
    image_retention_seconds: int = 60
    cache_ttl_hours: int = 24

    allowed_origins: str = "http://localhost:5173"

    class Config:
        env_file = ".env"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    return Settings()
