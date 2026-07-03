from typing import Literal

from pydantic import BaseModel, Field

from backend.app.tools.sql_template_tools import SalesTrendParameters


SqlGenerationPath = Literal["template_render", "deterministic_rewrite", "unsupported"]


class GeneratedSql(BaseModel):
    path: SqlGenerationPath
    sql: str = ""
    parameters: SalesTrendParameters | None = None
    warnings: list[str] = Field(default_factory=list)

