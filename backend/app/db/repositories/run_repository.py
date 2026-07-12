import json
from uuid import UUID

from backend.app.db.connection import get_connection
from backend.app.schemas.runs import (
    QueryRunCreate,
    QueryRunDetail,
    QueryRunRecord,
    ToolCallCreate,
    ToolCallRecord,
)


class RunRepository:
    """PostgreSQL 查询运行记录仓储。"""

    def create_run(self, payload: QueryRunCreate) -> QueryRunRecord:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO query_runs (
                  id, app_user_id, user_question, rewritten_question, memory_hit, memory_id,
                  generated_sql, final_sql, guard_status, execution_status,
                  row_count, latency_ms, error_message
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id, app_user_id, user_question, rewritten_question, memory_hit, memory_id,
                          generated_sql, final_sql, guard_status, execution_status,
                          row_count, latency_ms, error_message, created_at
                """,
                (
                    str(payload.id),
                    str(payload.app_user_id) if payload.app_user_id else None,
                    payload.user_question,
                    payload.rewritten_question,
                    payload.memory_hit,
                    str(payload.memory_id) if payload.memory_id else None,
                    payload.generated_sql,
                    payload.final_sql,
                    payload.guard_status,
                    payload.execution_status,
                    payload.row_count,
                    payload.latency_ms,
                    payload.error_message,
                ),
            )
            return _row_to_query_run(cursor.fetchone())

    def create_tool_call(self, payload: ToolCallCreate) -> ToolCallRecord:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO tool_calls (
                  id, query_run_id, tool_name, input_payload, output_payload,
                  status, latency_ms, error_message
                )
                VALUES (%s, %s, %s, %s::jsonb, %s::jsonb, %s, %s, %s)
                RETURNING id, query_run_id, tool_name, input_payload, output_payload,
                          status, latency_ms, error_message, created_at
                """,
                (
                    str(payload.id),
                    str(payload.query_run_id),
                    payload.tool_name,
                    json.dumps(payload.input_payload, ensure_ascii=False),
                    json.dumps(payload.output_payload, ensure_ascii=False),
                    payload.status,
                    payload.latency_ms,
                    payload.error_message,
                ),
            )
            return _row_to_tool_call(cursor.fetchone())

    def list_runs(self, limit: int = 20) -> list[QueryRunRecord]:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT id, app_user_id, user_question, rewritten_question, memory_hit, memory_id,
                       generated_sql, final_sql, guard_status, execution_status,
                       row_count, latency_ms, error_message, created_at
                FROM query_runs
                ORDER BY created_at DESC
                LIMIT %s
                """,
                (limit,),
            )
            return [_row_to_query_run(row) for row in cursor.fetchall()]

    def get_run(self, run_id: UUID) -> QueryRunDetail | None:
        run = self._get_run_record(run_id)
        if run is None:
            return None
        return QueryRunDetail(**run.model_dump(), tool_calls=self.list_tool_calls(run_id))

    def list_tool_calls(self, run_id: UUID) -> list[ToolCallRecord]:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT id, query_run_id, tool_name, input_payload, output_payload,
                       status, latency_ms, error_message, created_at
                FROM tool_calls
                WHERE query_run_id = %s
                ORDER BY created_at ASC
                """,
                (str(run_id),),
            )
            return [_row_to_tool_call(row) for row in cursor.fetchall()]

    def _get_run_record(self, run_id: UUID) -> QueryRunRecord | None:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT id, app_user_id, user_question, rewritten_question, memory_hit, memory_id,
                       generated_sql, final_sql, guard_status, execution_status,
                       row_count, latency_ms, error_message, created_at
                FROM query_runs
                WHERE id = %s
                """,
                (str(run_id),),
            )
            row = cursor.fetchone()
            return _row_to_query_run(row) if row else None


def _row_to_query_run(row) -> QueryRunRecord:
    return QueryRunRecord(
        id=row[0],
        app_user_id=row[1],
        user_question=row[2],
        rewritten_question=row[3],
        memory_hit=row[4],
        memory_id=row[5],
        generated_sql=row[6],
        final_sql=row[7],
        guard_status=row[8],
        execution_status=row[9],
        row_count=row[10],
        latency_ms=row[11],
        error_message=row[12],
        created_at=row[13],
    )


def _row_to_tool_call(row) -> ToolCallRecord:
    input_payload = _json_payload(row[3])
    output_payload = _json_payload(row[4])
    return ToolCallRecord(
        id=row[0],
        query_run_id=row[1],
        tool_name=row[2],
        input_payload=input_payload,
        output_payload=output_payload,
        status=row[5],
        latency_ms=row[6],
        error_message=row[7],
        created_at=row[8],
    )


def _json_payload(value) -> dict:
    if isinstance(value, str):
        return json.loads(value)
    return value or {}
