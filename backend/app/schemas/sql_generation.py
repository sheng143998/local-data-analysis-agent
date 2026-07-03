from typing import Literal

from pydantic import BaseModel, Field

from backend.app.tools.sql_template_tools import SalesTrendParameters


SqlGenerationPath = Literal[
    "template_render",
    "deterministic_rewrite",
    "model_generate",
    "model_rewrite",
    "model_error",
    "unsupported",
]


class GeneratedSql(BaseModel):
    path: SqlGenerationPath
    sql: str = ""
    parameters: SalesTrendParameters | None = None
    warnings: list[str] = Field(default_factory=list)
    model_provider: str = ""
    model_name: str = ""
    model_latency_ms: int = 0
