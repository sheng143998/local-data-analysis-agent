from typing import Any, Literal

from pydantic import BaseModel, Field


ExecutionStatus = Literal["success", "error", "blocked"]


class SqlExecutionResult(BaseModel):
    status: ExecutionStatus
    columns: list[str] = Field(default_factory=list)
    rows: list[dict[str, Any]] = Field(default_factory=list)
    row_count: int = 0
    latency_ms: int = 0
    error_message: str | None = None
