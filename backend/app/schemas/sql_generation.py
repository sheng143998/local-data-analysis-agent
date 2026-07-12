from typing import Any, Literal

from pydantic import BaseModel, Field


SqlGenerationPath = Literal[
    "memory_reuse",
    "memory_reuse_verified",
    "model_generate",
    "model_rewrite",
    "model_repair",
    "model_error",
    "unsupported",
]


class GeneratedSql(BaseModel):
    path: SqlGenerationPath
    sql: str = ""
    parameters: dict[str, Any] | None = None
    warnings: list[str] = Field(default_factory=list)
    model_provider: str = ""
    model_name: str = ""
    model_latency_ms: int = 0
