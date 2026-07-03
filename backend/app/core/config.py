import os

from pydantic import BaseModel, Field


def _env_bool(name: str, *, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


class Settings(BaseModel):
    app_version: str = "0.1.0"
    cors_origins: list[str] = ["http://localhost:5173", "http://127.0.0.1:5173"]
    model_provider: str = Field(default_factory=lambda: os.getenv("MODEL_PROVIDER", "local"))
    model_base_url: str = Field(
        default_factory=lambda: os.getenv(
            "MODEL_BASE_URL",
            "http://127.0.0.1:11434/v1",
        )
    )
    model_name: str = Field(default_factory=lambda: os.getenv("MODEL_NAME", "local-sql-model"))
    model_api_key: str = Field(default_factory=lambda: os.getenv("MODEL_API_KEY", ""))
    model_timeout_seconds: float = Field(
        default_factory=lambda: float(os.getenv("MODEL_TIMEOUT_SECONDS", "30"))
    )
    model_max_retries: int = Field(default_factory=lambda: int(os.getenv("MODEL_MAX_RETRIES", "1")))
    model_sql_generator_enabled: bool = Field(
        default_factory=lambda: _env_bool("MODEL_SQL_GENERATOR_ENABLED", default=False)
    )


settings = Settings()
