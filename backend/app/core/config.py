import os

from dotenv import load_dotenv
from pydantic import BaseModel, Field


load_dotenv("backend/.env")


def _env_bool(name: str, *, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _env_first(*names: str, default: str = "") -> str:
    for name in names:
        value = os.getenv(name)
        if value and value.strip() and value.strip() != "change_me":
            return value.strip()
    return default


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
    model_name: str = Field(default_factory=lambda: os.getenv("MODEL_NAME", "qwen2.5-coder:3b"))
    model_api_key: str = Field(default_factory=lambda: _env_first("MODEL_API_KEY"))
    model_timeout_seconds: float = Field(
        default_factory=lambda: float(os.getenv("MODEL_TIMEOUT_SECONDS", "30"))
    )
    model_max_retries: int = Field(default_factory=lambda: int(os.getenv("MODEL_MAX_RETRIES", "1")))
    model_sql_generator_enabled: bool = Field(
        default_factory=lambda: _env_bool("MODEL_SQL_GENERATOR_ENABLED", default=False)
    )
    intent_parser_enabled: bool = Field(default_factory=lambda: _env_bool("INTENT_PARSER_ENABLED", default=True))
    intent_model_provider: str = Field(
        default_factory=lambda: os.getenv("INTENT_MODEL_PROVIDER", os.getenv("MODEL_PROVIDER", "local"))
    )
    intent_model_base_url: str = Field(
        default_factory=lambda: os.getenv(
            "INTENT_MODEL_BASE_URL",
            os.getenv("MODEL_BASE_URL", "http://127.0.0.1:11434/v1"),
        )
    )
    intent_model_name: str = Field(
        default_factory=lambda: os.getenv("INTENT_MODEL_NAME", os.getenv("MODEL_NAME", "qwen2.5-coder:3b"))
    )
    intent_model_api_key: str = Field(default_factory=lambda: _env_first("INTENT_MODEL_API_KEY", "MODEL_API_KEY"))
    intent_model_timeout_seconds: float = Field(
        default_factory=lambda: float(os.getenv("INTENT_MODEL_TIMEOUT_SECONDS", os.getenv("MODEL_TIMEOUT_SECONDS", "30")))
    )
    intent_model_max_retries: int = Field(
        default_factory=lambda: int(os.getenv("INTENT_MODEL_MAX_RETRIES", os.getenv("MODEL_MAX_RETRIES", "1")))
    )
    embedding_provider: str = Field(default_factory=lambda: os.getenv("EMBEDDING_PROVIDER", "aliyun"))
    embedding_base_url: str = Field(
        default_factory=lambda: os.getenv(
            "EMBEDDING_BASE_URL",
            "https://dashscope.aliyuncs.com/compatible-mode/v1",
        )
    )
    embedding_model: str = Field(default_factory=lambda: os.getenv("EMBEDDING_MODEL", "text-embedding-v4"))
    embedding_api_key: str = Field(
        default_factory=lambda: _env_first(
            "EMBEDDING_API_KEY",
            "DASHSCOPE_API_KEY",
            "DASH_SCOPE_API_KEY",
            "ALIYUN_API_KEY",
            "MODEL_API_KEY",
        )
    )
    embedding_dimensions: int = Field(default_factory=lambda: int(os.getenv("EMBEDDING_DIMENSIONS", "1536")))
    embedding_timeout_seconds: float = Field(
        default_factory=lambda: float(os.getenv("EMBEDDING_TIMEOUT_SECONDS", os.getenv("MODEL_TIMEOUT_SECONDS", "30")))
    )
    embedding_max_retries: int = Field(
        default_factory=lambda: int(os.getenv("EMBEDDING_MAX_RETRIES", os.getenv("MODEL_MAX_RETRIES", "1")))
    )


settings = Settings()
