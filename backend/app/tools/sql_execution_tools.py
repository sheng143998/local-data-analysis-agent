from datetime import date, datetime
from decimal import Decimal
from time import perf_counter
from typing import Any

from backend.app.db.connection import get_connection
from backend.app.core.config import settings
from backend.app.schemas.sql_execution import SqlExecutionResult
from backend.app.schemas.sql_validation import SqlGuardResult


ERROR_CATEGORY_MESSAGES = {
    "group_by": "SQL 聚合分组不完整，我会尝试补齐 GROUP BY 或改写聚合口径。",
    "missing_column": "SQL 使用了当前数据表中不存在的字段，我会尝试改用已登记的字段。",
    "missing_table": "SQL 使用了当前数据库中不存在的表，我会尝试改用可用的数据表。",
    "type_cast": "SQL 中存在类型转换问题，我会尝试改写类型处理方式。",
    "division_by_zero": "SQL 执行时出现除零问题，我会尝试补充 NULLIF 等保护。",
    "syntax": "SQL 语法不符合 PostgreSQL 要求，我会尝试重新生成查询。",
    "runtime": "数据库执行查询时返回错误，我会尝试根据错误信息修复 SQL。",
}


def execute_guarded_sql(guard_result: SqlGuardResult) -> SqlExecutionResult:
    if not guard_result.allowed or not guard_result.final_sql:
        return SqlExecutionResult(
            status="blocked",
            error_message="SQL Guard 未放行，Executor 拒绝执行",
            error_category="guard_blocked",
            user_error_message="这条查询没有通过只读安全校验，因此没有执行。",
        )

    start = perf_counter()
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("BEGIN TRANSACTION READ ONLY")
            cursor.execute(f"SET LOCAL statement_timeout = '{settings.sql_statement_timeout_ms}ms'")
            cursor.execute(f"SET LOCAL lock_timeout = '{settings.sql_lock_timeout_ms}ms'")
            cursor.execute(guard_result.final_sql)
            columns = [item[0] for item in cursor.description or []]
            raw_rows = cursor.fetchall()
            rows = [dict(zip(columns, [_to_jsonable(value) for value in row])) for row in raw_rows]
            conn.rollback()
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
        error_message = str(exc)
        error_category = classify_sql_execution_error(error_message)
        return SqlExecutionResult(
            status="error",
            latency_ms=latency_ms,
            error_message=error_message,
            error_category=error_category,
            user_error_message=ERROR_CATEGORY_MESSAGES[error_category],
        )


def _to_jsonable(value: Any) -> Any:
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, datetime | date):
        return value.isoformat()
    return value


def classify_sql_execution_error(error_message: str) -> str:
    lowered = error_message.lower()
    if (
        "must appear in the group by clause" in lowered
        or "42803" in lowered
        or "group by" in lowered and "aggregate" in lowered
    ):
        return "group_by"
    if (
        "column" in lowered
        and ("does not exist" in lowered or "missing from" in lowered)
    ) or "undefinedcolumn" in lowered or "42703" in lowered or "字段" in error_message and "不存在" in error_message:
        return "missing_column"
    if (
        "relation" in lowered
        and "does not exist" in lowered
        or "undefinedtable" in lowered
        or "42p01" in lowered
        or "关系" in error_message and "不存在" in error_message
    ):
        return "missing_table"
    if (
        "invalid input syntax" in lowered
        or "cannot cast" in lowered
        or "operator does not exist" in lowered
        or "datatype mismatch" in lowered
        or "type" in lowered and "cannot be cast" in lowered
        or "22p02" in lowered
        or "42846" in lowered
        or "类型" in error_message and "转换" in error_message
    ):
        return "type_cast"
    if "division by zero" in lowered or "divide by zero" in lowered or "22012" in lowered or "除以零" in error_message:
        return "division_by_zero"
    if "syntax error" in lowered or "parse" in lowered:
        return "syntax"
    return "runtime"
