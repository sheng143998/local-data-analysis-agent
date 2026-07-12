import os
from uuid import UUID, uuid5

from dotenv import load_dotenv
from pydantic import BaseModel, Field


# 本项目本地服务始终以 backend/.env 为准，避免旧终端变量让登录与会话归属配置失效。
load_dotenv("backend/.env", override=True)


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
    cors_origins: list[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:3002",
        "http://127.0.0.1:3002",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ]
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
    sql_max_rows: int = Field(default_factory=lambda: int(os.getenv("SQL_MAX_ROWS", "30")), ge=1)
    sql_statement_timeout_ms: int = Field(
        default_factory=lambda: int(os.getenv("SQL_STATEMENT_TIMEOUT_MS", "15000"))
    )
    sql_lock_timeout_ms: int = Field(
        default_factory=lambda: int(os.getenv("SQL_LOCK_TIMEOUT_MS", "3000"))
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
    app_env: str = Field(default_factory=lambda: os.getenv("APP_ENV", "local").strip().lower())
    auth_required: bool = Field(default_factory=lambda: _env_bool("AUTH_REQUIRED", default=False))
    auth_allow_self_registration: bool = Field(default_factory=lambda: _env_bool("AUTH_ALLOW_SELF_REGISTRATION", default=False))
    auth_session_idle_hours: int = Field(default_factory=lambda: int(os.getenv("AUTH_SESSION_IDLE_HOURS", "12")), ge=1, le=168)
    auth_session_absolute_days: int = Field(default_factory=lambda: int(os.getenv("AUTH_SESSION_ABSOLUTE_DAYS", "7")), ge=1, le=90)
    auth_cookie_name: str = Field(default_factory=lambda: os.getenv("AUTH_COOKIE_NAME", "local_data_agent_session"))
    auth_csrf_cookie_name: str = Field(default_factory=lambda: os.getenv("AUTH_CSRF_COOKIE_NAME", "local_data_agent_csrf"))
    auth_cookie_secure: bool = Field(default_factory=lambda: _env_bool("AUTH_COOKIE_SECURE", default=False))
    auth_dev_user_email: str = Field(default_factory=lambda: os.getenv("AUTH_DEV_USER_EMAIL", "local-admin@localhost"))
    redis_url: str = Field(default_factory=lambda: os.getenv("REDIS_URL", "redis://127.0.0.1:6379/0"))
    conversation_retention_hours: int = Field(
        default_factory=lambda: int(os.getenv("CONVERSATION_RETENTION_HOURS", "72")), ge=1, le=168
    )
    conversation_message_limit: int = Field(
        default_factory=lambda: int(os.getenv("CONVERSATION_MESSAGE_LIMIT", "200")), ge=10, le=1000
    )
    conversation_context_token_budget: int = Field(
        default_factory=lambda: int(os.getenv("CONVERSATION_CONTEXT_TOKEN_BUDGET", "8000")), ge=1000
    )
    conversation_output_token_reserve: int = Field(
        default_factory=lambda: int(os.getenv("CONVERSATION_OUTPUT_TOKEN_RESERVE", "1000")), ge=0
    )
    conversation_compression_light_watermark: float = Field(
        default_factory=lambda: float(os.getenv("CONVERSATION_COMPRESSION_LIGHT_WATERMARK", "0.6")), ge=0.1, le=1
    )
    conversation_compression_aggressive_watermark: float = Field(
        default_factory=lambda: float(os.getenv("CONVERSATION_COMPRESSION_AGGRESSIVE_WATERMARK", "0.8")), ge=0.1, le=1
    )
    conversation_summary_char_limit: int = Field(
        default_factory=lambda: int(os.getenv("CONVERSATION_SUMMARY_CHAR_LIMIT", "6000")), ge=256
    )
    auth_login_rate_limit_per_15_minutes: int = Field(
        default_factory=lambda: int(os.getenv("AUTH_LOGIN_RATE_LIMIT_PER_15_MINUTES", "10")), ge=1
    )
    auth_register_rate_limit_per_hour: int = Field(
        default_factory=lambda: int(os.getenv("AUTH_REGISTER_RATE_LIMIT_PER_HOUR", "5")), ge=1
    )

    def validate_security(self) -> None:
        if self.app_env in {"production", "prod"} and not self.auth_required:
            raise RuntimeError("Production requires AUTH_REQUIRED=true")
        if self.app_env in {"production", "prod"} and not self.auth_cookie_secure:
            raise RuntimeError("Production requires AUTH_COOKIE_SECURE=true")
        if self.app_env in {"production", "prod"} and not self.redis_url:
            raise RuntimeError("Production requires REDIS_URL for conversation memory")

    @property
    def development_principal_id(self) -> UUID:
        return uuid5(UUID("6ba7b810-9dad-11d1-80b4-00c04fd430c8"), self.auth_dev_user_email.lower())


settings = Settings()
