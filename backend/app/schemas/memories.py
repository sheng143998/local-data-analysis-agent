from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field

from backend.app.schemas.analysis import PathType


ReuseType = Literal[
    "none",
    "direct_reuse",
    "parameter_rewrite",
    "dimension_extend",
    "filter_extend",
    "subquery_reuse",
    "regenerate",
]


class SqlMemoryRecord(BaseModel):
    id: UUID
    canonical_question: str
    normalized_question: str
    question_pattern: str = ""
    intent: str = ""
    sql_template: str
    final_sql: str
    param_schema: dict = Field(default_factory=dict)
    parameters: dict = Field(default_factory=dict)
    tables: list[str] = Field(default_factory=list)
    metrics: list[str] = Field(default_factory=list)
    dimensions: list[str] = Field(default_factory=list)
    filters: dict = Field(default_factory=dict)
    dialect: str = "postgresql"
    schema_version: str = "v1"
    success_count: int = 0
    failure_count: int = 0
    avg_latency_ms: int = 0
    last_result_columns: list[str] = Field(default_factory=list)
    last_row_count: int = 0
    last_used_at: datetime | None = None
    created_at: datetime


class SqlMemoryCandidate(BaseModel):
    memory: SqlMemoryRecord
    score: float
    semantic_similarity: float
    text_similarity: float
    metric_table_match: float
    success_score: float
    required_table_match: bool = True
    required_tables: list[str] = Field(default_factory=list)


class SqlReusePlan(BaseModel):
    path_type: PathType = "cold_path"
    reuse_type: ReuseType = "none"
    memory_hit: bool = False
    selected_memory_id: UUID | None = None
    selected_sql: str | None = None
    candidate_count: int = 0
    score: float = 0


class SqlMemoryUpsert(BaseModel):
    canonical_question: str
    sql_template: str
    final_sql: str
    parameters: dict = Field(default_factory=dict)
    tables: list[str] = Field(default_factory=list)
    metrics: list[str] = Field(default_factory=list)
    dimensions: list[str] = Field(default_factory=list)
    result_columns: list[str] = Field(default_factory=list)
    row_count: int = 0
    latency_ms: int = 0
