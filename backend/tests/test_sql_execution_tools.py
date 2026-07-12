from contextlib import contextmanager

from backend.app.schemas.sql_validation import SqlGuardResult
from backend.app.tools import sql_execution_tools
from backend.app.tools.sql_execution_tools import classify_sql_execution_error, execute_guarded_sql
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
    guard = guard_sql("SELECT 1 / 0 AS broken FROM orders", max_rows=1)
    result = execute_guarded_sql(guard)

    assert result.status == "error"
    assert result.error_message
    assert result.error_category == "division_by_zero"
    assert result.user_error_message
    assert "除零" in result.user_error_message
    assert "division by zero" not in result.user_error_message


def test_classify_sql_execution_errors() -> None:
    assert classify_sql_execution_error('column "foo" does not exist') == "missing_column"
    assert classify_sql_execution_error('relation "foo" does not exist') == "missing_table"
    assert classify_sql_execution_error("must appear in the GROUP BY clause") == "group_by"
    assert classify_sql_execution_error("invalid input syntax for type numeric") == "type_cast"


def test_executor_uses_read_only_transaction_and_timeouts(monkeypatch) -> None:
    class FakeCursor:
        description = [("id",)]

        def __init__(self) -> None:
            self.calls: list[tuple[str, tuple[str, ...] | None]] = []

        def execute(self, sql: str, params=None) -> None:
            self.calls.append((sql, params))

        def fetchall(self):
            return [(1,)]

    class FakeConnection:
        def __init__(self) -> None:
            self.cursor_instance = FakeCursor()
            self.rolled_back = False

        def cursor(self) -> FakeCursor:
            return self.cursor_instance

        def rollback(self) -> None:
            self.rolled_back = True

    connection = FakeConnection()

    @contextmanager
    def fake_get_connection():
        yield connection

    monkeypatch.setattr(sql_execution_tools, "get_connection", fake_get_connection)
    monkeypatch.setattr(sql_execution_tools.settings, "sql_statement_timeout_ms", 2500)
    monkeypatch.setattr(sql_execution_tools.settings, "sql_lock_timeout_ms", 500)

    result = execute_guarded_sql(SqlGuardResult(allowed=True, final_sql="SELECT id FROM orders LIMIT 1"))

    assert result.status == "success"
    assert connection.rolled_back is True
    assert connection.cursor_instance.calls == [
        ("BEGIN TRANSACTION READ ONLY", None),
        ("SET LOCAL statement_timeout = '2500ms'", None),
        ("SET LOCAL lock_timeout = '500ms'", None),
        ("SELECT id FROM orders LIMIT 1", None),
    ]
