from datetime import date, datetime
from decimal import Decimal
from time import perf_counter
from typing import Any

from backend.app.db.connection import get_connection
from backend.app.schemas.sql_execution import SqlExecutionResult
from backend.app.schemas.sql_validation import SqlGuardResult


def execute_guarded_sql(guard_result: SqlGuardResult) -> SqlExecutionResult:
    if not guard_result.allowed or not guard_result.final_sql:
        return SqlExecutionResult(
            status="blocked",
            error_message="SQL Guard 未放行，Executor 拒绝执行",
        )

    start = perf_counter()
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(guard_result.final_sql)
            columns = [item[0] for item in cursor.description or []]
            raw_rows = cursor.fetchall()
            rows = [dict(zip(columns, [_to_jsonable(value) for value in row])) for row in raw_rows]
        latency_ms = int((perf_counter() - start) * 1000)
        return SqlExecutionResult(
            status="success",
            columns=columns,
            rows=rows,
            row_count=len(rows),
            latency_ms=latency_ms,
        )
    except Exception as exc:
        latency_ms = int((perf_counter() - start) * 1000)
        return SqlExecutionResult(
            status="error",
            latency_ms=latency_ms,
            error_message=str(exc),
        )


def _to_jsonable(value: Any) -> Any:
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, datetime | date):
        return value.isoformat()
    return value
