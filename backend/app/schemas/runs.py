from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class ToolCallRecord(BaseModel):
    id: UUID
    query_run_id: UUID | None = None
    tool_name: str
    input_payload: dict[str, Any] = Field(default_factory=dict)
    output_payload: dict[str, Any] = Field(default_factory=dict)
    status: str
    latency_ms: int = 0
    error_message: str | None = None
    created_at: datetime


class QueryRunRecord(BaseModel):
    id: UUID
    user_question: str
    rewritten_question: str | None = None
    memory_hit: bool = False
    memory_id: UUID | None = None
    generated_sql: str | None = None
    final_sql: str | None = None
    guard_status: str
    execution_status: str
    row_count: int = 0
    latency_ms: int = 0
    error_message: str | None = None
    created_at: datetime


class QueryRunDetail(QueryRunRecord):
    tool_calls: list[ToolCallRecord] = Field(default_factory=list)
    debug_summary: dict[str, Any] = Field(default_factory=dict)


class QueryRunCreate(BaseModel):
    id: UUID
    user_question: str
    rewritten_question: str | None = None
    memory_hit: bool = False
    memory_id: UUID | None = None
    generated_sql: str | None = None
    final_sql: str | None = None
    guard_status: str = "pending"
    execution_status: str = "pending"
    row_count: int = 0
    latency_ms: int = 0
    error_message: str | None = None


class ToolCallCreate(BaseModel):
    id: UUID
    query_run_id: UUID
    tool_name: str
    input_payload: dict[str, Any] = Field(default_factory=dict)
    output_payload: dict[str, Any] = Field(default_factory=dict)
    status: str
    latency_ms: int = 0
    error_message: str | None = None
