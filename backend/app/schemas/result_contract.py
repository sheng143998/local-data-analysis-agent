from typing import Any

from pydantic import BaseModel, Field


class ResultColumn(BaseModel):
    name: str
    semantic_role: str = "unknown"


class ResultContract(BaseModel):
    resolved_question: str
    query_plan: dict[str, Any] = Field(default_factory=dict)
    columns: list[ResultColumn] = Field(default_factory=list)
    rows: list[dict[str, Any]] = Field(default_factory=list)
    row_count: int = 0
    time_range: str = ""
    warnings: list[str] = Field(default_factory=list)
