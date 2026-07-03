from backend.app.tools.sql_execution_tools import execute_guarded_sql
from backend.app.tools.sql_validation_tools import guard_sql


def test_execute_guarded_sql_success() -> None:
    guard = guard_sql("SELECT id, status FROM orders ORDER BY created_at DESC", max_rows=3)
    result = execute_guarded_sql(guard)

    assert result.status == "success"
    assert result.columns == ["id", "status"]
    assert result.row_count <= 3


def test_executor_rejects_blocked_guard_result() -> None:
    guard = guard_sql("DELETE FROM orders WHERE id = '1'")
    result = execute_guarded_sql(guard)

    assert result.status == "blocked"
    assert result.error_message == "SQL Guard 未放行，Executor 拒绝执行"


def test_execute_guarded_sql_returns_error_for_runtime_issue() -> None:
    guard = guard_sql("SELECT missing_column FROM orders", max_rows=1)
    result = execute_guarded_sql(guard)

    assert result.status == "error"
    assert result.error_message
