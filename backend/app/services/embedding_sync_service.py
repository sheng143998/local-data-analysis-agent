from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any, Literal

from backend.app.core.embedding_adapter import EmbeddingAdapter, EmbeddingRequest
from backend.app.db.connection import get_connection


EmbeddingTarget = Literal["schema", "metric", "memory"]


@dataclass(frozen=True)
class SchemaEmbeddingRecord:
    table_name: str
    column_name: str
    data_type: str
    description: str
    business_meaning: str


@dataclass(frozen=True)
class MetricEmbeddingRecord:
    id: str
    metric_name: str
    display_name: str
    description: str
    formula: str
    required_tables: list[str]
    required_fields: list[str]
    default_filters: dict[str, Any]


@dataclass(frozen=True)
class SqlMemoryEmbeddingRecord:
    id: str
    canonical_question: str
    final_sql: str


@dataclass
class EmbeddingSyncResult:
    target: EmbeddingTarget
    scanned: int = 0
    updated: int = 0
    failed: int = 0
    errors: list[str] = field(default_factory=list)


class EmbeddingSyncService:
    """同步 schema 和 metric 文档 embedding 到 PostgreSQL pgvector 字段。"""

    def __init__(self, adapter: EmbeddingAdapter | None = None) -> None:
        self.adapter = adapter or EmbeddingAdapter()

    def sync_schema_embeddings(self) -> EmbeddingSyncResult:
        result = EmbeddingSyncResult(target="schema")
        with get_connection() as conn:
            cursor = conn.cursor()
            records = self._load_schema_records(cursor)
            result.scanned = len(records)
            for record in records:
                document = build_schema_embedding_document(record)
                response = self.adapter.embed(EmbeddingRequest(texts=[document]))
                if not response.ok or not response.vectors:
                    result.failed += 1
                    result.errors.append(_error_summary("schema", record.table_name, record.column_name, response.error_message))
                    continue
                self._update_schema_embedding(cursor, record, response.vectors[0])
                result.updated += 1
        return result

    def sync_metric_embeddings(self) -> EmbeddingSyncResult:
        result = EmbeddingSyncResult(target="metric")
        with get_connection() as conn:
            cursor = conn.cursor()
            records = self._load_metric_records(cursor)
            result.scanned = len(records)
            for record in records:
                document = build_metric_embedding_document(record)
                response = self.adapter.embed(EmbeddingRequest(texts=[document]))
                if not response.ok or not response.vectors:
                    result.failed += 1
                    result.errors.append(_error_summary("metric", record.metric_name, None, response.error_message))
                    continue
                self._update_metric_embedding(cursor, record, response.vectors[0])
                result.updated += 1
        return result

    def sync_all(self) -> list[EmbeddingSyncResult]:
        return [
            self.sync_schema_embeddings(),
            self.sync_metric_embeddings(),
            self.sync_sql_memory_embeddings(),
        ]

    def sync_sql_memory_embeddings(self) -> EmbeddingSyncResult:
        result = EmbeddingSyncResult(target="memory")
        with get_connection() as conn:
            cursor = conn.cursor()
            records = self._load_sql_memory_records(cursor)
            result.scanned = len(records)
            for record in records:
                response = self.adapter.embed(
                    EmbeddingRequest(texts=[record.canonical_question, record.final_sql])
                )
                if not response.ok or len(response.vectors) < 2:
                    result.failed += 1
                    result.errors.append(_error_summary("memory", record.id, None, response.error_message))
                    continue
                self._update_sql_memory_embeddings(
                    cursor,
                    record,
                    question_vector=response.vectors[0],
                    sql_vector=response.vectors[1],
                )
                result.updated += 1
        return result

    def _load_schema_records(self, cursor) -> list[SchemaEmbeddingRecord]:
        cursor.execute(
            """
            SELECT table_name, column_name, data_type, description, business_meaning
            FROM schema_metadata
            ORDER BY table_name, column_name
            """
        )
        return [
            SchemaEmbeddingRecord(
                table_name=row[0],
                column_name=row[1],
                data_type=row[2],
                description=row[3] or "",
                business_meaning=row[4] or "",
            )
            for row in cursor.fetchall()
        ]

    def _load_metric_records(self, cursor) -> list[MetricEmbeddingRecord]:
        cursor.execute(
            """
            SELECT id, metric_name, display_name, description, formula,
                   required_tables, required_fields, default_filters
            FROM metric_definitions
            WHERE status = 'enabled'
            ORDER BY display_name
            """
        )
        return [
            MetricEmbeddingRecord(
                id=str(row[0]),
                metric_name=row[1],
                display_name=row[2],
                description=row[3] or "",
                formula=row[4] or "",
                required_tables=list(row[5] or []),
                required_fields=list(row[6] or []),
                default_filters=_json_object(row[7]),
            )
            for row in cursor.fetchall()
        ]

    def _update_schema_embedding(
        self,
        cursor,
        record: SchemaEmbeddingRecord,
        vector: list[float],
    ) -> None:
        cursor.execute(
            """
            UPDATE schema_metadata
            SET embedding = %s::vector,
                updated_at = now()
            WHERE table_name = %s AND column_name = %s
            """,
            (_vector_literal(vector), record.table_name, record.column_name),
        )

    def _update_metric_embedding(
        self,
        cursor,
        record: MetricEmbeddingRecord,
        vector: list[float],
    ) -> None:
        cursor.execute(
            """
            UPDATE metric_definitions
            SET embedding = %s::vector,
                updated_at = now()
            WHERE id = %s
            """,
            (_vector_literal(vector), record.id),
        )

    def _load_sql_memory_records(self, cursor) -> list[SqlMemoryEmbeddingRecord]:
        cursor.execute(
            """
            SELECT id, canonical_question, final_sql
            FROM sql_memories
            WHERE question_embedding IS NULL OR sql_embedding IS NULL
            ORDER BY last_used_at DESC NULLS LAST, created_at DESC
            """
        )
        return [
            SqlMemoryEmbeddingRecord(
                id=str(row[0]),
                canonical_question=row[1] or "",
                final_sql=row[2] or "",
            )
            for row in cursor.fetchall()
        ]

    def _update_sql_memory_embeddings(
        self,
        cursor,
        record: SqlMemoryEmbeddingRecord,
        *,
        question_vector: list[float],
        sql_vector: list[float],
    ) -> None:
        cursor.execute(
            """
            UPDATE sql_memories
            SET question_embedding = %s::vector,
                sql_embedding = %s::vector
            WHERE id = %s
            """,
            (_vector_literal(question_vector), _vector_literal(sql_vector), record.id),
        )


def build_schema_embedding_document(record: SchemaEmbeddingRecord) -> str:
    return "\n".join(
        [
            f"表名: {record.table_name}",
            f"字段名: {record.column_name}",
            f"字段类型: {record.data_type}",
            f"字段说明: {record.description}",
            f"业务含义: {record.business_meaning}",
        ]
    )


def build_metric_embedding_document(record: MetricEmbeddingRecord) -> str:
    return "\n".join(
        [
            f"指标编码: {record.metric_name}",
            f"指标名称: {record.display_name}",
            f"指标说明: {record.description}",
            f"计算公式: {record.formula}",
            f"依赖数据表: {', '.join(record.required_tables)}",
            f"依赖字段: {', '.join(record.required_fields)}",
            f"默认过滤: {json.dumps(record.default_filters, ensure_ascii=False, sort_keys=True)}",
        ]
    )


def _vector_literal(vector: list[float]) -> str:
    return "[" + ",".join(f"{float(value):.8f}" for value in vector) + "]"


def _json_object(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return value
    if isinstance(value, str):
        try:
            parsed = json.loads(value)
        except json.JSONDecodeError:
            return {}
        return parsed if isinstance(parsed, dict) else {}
    return {}


def _error_summary(target: str, name: str, column: str | None, error: str | None) -> str:
    identifier = f"{name}.{column}" if column else name
    return f"{target}:{identifier}: {error or 'embedding failed'}"
