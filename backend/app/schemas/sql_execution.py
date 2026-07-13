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
    error_category: str | None = None
    user_error_message: str | None = None


class SqlExplainResult(BaseModel):
    """SQL 主查询前的 PostgreSQL 规划预检结果，不持久化完整执行计划。"""

    status: ExecutionStatus
    latency_ms: int = 0
    error_message: str | None = None
    error_category: str | None = None
    user_error_message: str | None = None
