import json
from uuid import UUID, uuid4

from backend.app.db.connection import get_connection
from backend.app.schemas.memories import SqlMemoryRecord, SqlMemoryUpsert
from backend.app.tools.text_normalization import normalize_question


class SqlMemoryRepository:
    """PostgreSQL SQL Memory 仓储。"""

    def list(self, limit: int = 50) -> list[SqlMemoryRecord]:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT id, canonical_question, normalized_question, question_pattern,
                       intent, sql_template, final_sql, param_schema, parameters,
                       tables, metrics, dimensions, filters, dialect, schema_version,
                       success_count, failure_count, avg_latency_ms, last_result_columns,
                       last_row_count, last_used_at, created_at
                FROM sql_memories
                ORDER BY last_used_at DESC NULLS LAST, created_at DESC
                LIMIT %s
                """,
                (limit,),
            )
            return [_row_to_memory(row) for row in cursor.fetchall()]

    def get(self, memory_id: UUID) -> SqlMemoryRecord | None:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT id, canonical_question, normalized_question, question_pattern,
                       intent, sql_template, final_sql, param_schema, parameters,
                       tables, metrics, dimensions, filters, dialect, schema_version,
                       success_count, failure_count, avg_latency_ms, last_result_columns,
                       last_row_count, last_used_at, created_at
                FROM sql_memories
                WHERE id = %s
                """,
                (str(memory_id),),
            )
            row = cursor.fetchone()
            return _row_to_memory(row) if row else None

    def upsert_success(self, payload: SqlMemoryUpsert) -> SqlMemoryRecord:
        normalized_question = normalize_question(payload.canonical_question)
        existing = self._get_by_normalized_question(normalized_question)
        if existing is None:
            return self._create_success(payload, normalized_question)
        return self._update_success(existing, payload)

    def _get_by_normalized_question(self, normalized_question: str) -> SqlMemoryRecord | None:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT id, canonical_question, normalized_question, question_pattern,
                       intent, sql_template, final_sql, param_schema, parameters,
                       tables, metrics, dimensions, filters, dialect, schema_version,
                       success_count, failure_count, avg_latency_ms, last_result_columns,
                       last_row_count, last_used_at, created_at
                FROM sql_memories
                WHERE normalized_question = %s
                ORDER BY created_at DESC
                LIMIT 1
                """,
                (normalized_question,),
            )
            row = cursor.fetchone()
            return _row_to_memory(row) if row else None

    def _create_success(
        self,
        payload: SqlMemoryUpsert,
        normalized_question: str,
    ) -> SqlMemoryRecord:
        memory_id = uuid4()
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO sql_memories (
                  id, canonical_question, normalized_question, question_pattern,
                  intent, sql_template, final_sql, question_embedding, sql_embedding,
                  param_schema, parameters,
                  tables, metrics, dimensions, filters, dialect, schema_version,
                  success_count, failure_count, avg_latency_ms, last_result_columns,
                  last_row_count, last_used_at
                )
                VALUES (
                  %s, %s, %s, '', 'sales_trend', %s, %s, %s::vector, %s::vector, '{}'::jsonb, %s::jsonb,
                  %s, %s, %s, %s::jsonb, 'postgresql', 'v1',
                  1, 0, %s, %s, %s, now()
                )
                RETURNING id, canonical_question, normalized_question, question_pattern,
                          intent, sql_template, final_sql, param_schema, parameters,
                          tables, metrics, dimensions, filters, dialect, schema_version,
                          success_count, failure_count, avg_latency_ms, last_result_columns,
                          last_row_count, last_used_at, created_at
                """,
                (
                    str(memory_id),
                    payload.canonical_question,
                    normalized_question,
                    payload.sql_template,
                    payload.final_sql,
                    _vector_literal(payload.question_embedding),
                    _vector_literal(payload.sql_embedding),
                    json.dumps(payload.parameters, ensure_ascii=False),
                    payload.tables,
                    payload.metrics,
                    payload.dimensions,
                    json.dumps({"trust_status": payload.trust_status}, ensure_ascii=False),
                    payload.latency_ms,
                    payload.result_columns,
                    payload.row_count,
                ),
            )
            return _row_to_memory(cursor.fetchone())

    def _update_success(
        self,
        existing: SqlMemoryRecord,
        payload: SqlMemoryUpsert,
    ) -> SqlMemoryRecord:
        next_success_count = existing.success_count + 1
        next_avg_latency = round(
            ((existing.avg_latency_ms * existing.success_count) + payload.latency_ms)
            / next_success_count
        )
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                UPDATE sql_memories
                SET canonical_question = %s,
                    sql_template = %s,
                    final_sql = %s,
                    question_embedding = COALESCE(%s::vector, question_embedding),
                    sql_embedding = COALESCE(%s::vector, sql_embedding),
                    parameters = %s::jsonb,
                    tables = %s,
                    metrics = %s,
                    dimensions = %s,
                    filters = %s::jsonb,
                    success_count = %s,
                    avg_latency_ms = %s,
                    last_result_columns = %s,
                    last_row_count = %s,
                    last_used_at = now()
                WHERE id = %s
                RETURNING id, canonical_question, normalized_question, question_pattern,
                          intent, sql_template, final_sql, param_schema, parameters,
                          tables, metrics, dimensions, filters, dialect, schema_version,
                          success_count, failure_count, avg_latency_ms, last_result_columns,
                          last_row_count, last_used_at, created_at
                """,
                (
                    payload.canonical_question,
                    payload.sql_template,
                    payload.final_sql,
                    _vector_literal(payload.question_embedding),
                    _vector_literal(payload.sql_embedding),
                    json.dumps(payload.parameters, ensure_ascii=False),
                    payload.tables,
                    payload.metrics,
                    payload.dimensions,
                    json.dumps({"trust_status": payload.trust_status}, ensure_ascii=False),
                    next_success_count,
                    next_avg_latency,
                    payload.result_columns,
                    payload.row_count,
                    str(existing.id),
                ),
            )
            return _row_to_memory(cursor.fetchone())


def _row_to_memory(row) -> SqlMemoryRecord:
    filters = _json_payload(row[12])
    return SqlMemoryRecord(
        id=row[0],
        canonical_question=row[1],
        normalized_question=row[2],
        question_pattern=row[3],
        intent=row[4],
        sql_template=row[5],
        final_sql=row[6],
        param_schema=_json_payload(row[7]),
        parameters=_json_payload(row[8]),
        tables=list(row[9] or []),
        metrics=list(row[10] or []),
        dimensions=list(row[11] or []),
        filters=filters,
        dialect=row[13],
        schema_version=row[14],
        trust_status=filters.get("trust_status", "reviewed"),
        success_count=row[15],
        failure_count=row[16],
        avg_latency_ms=row[17],
        last_result_columns=list(row[18] or []),
        last_row_count=row[19],
        last_used_at=row[20],
        created_at=row[21],
    )


def _json_payload(value) -> dict:
    if isinstance(value, str):
        return json.loads(value)
    return value or {}


def _vector_literal(vector: list[float] | None) -> str | None:
    if not vector:
        return None
    return "[" + ",".join(f"{float(value):.8f}" for value in vector) + "]"
