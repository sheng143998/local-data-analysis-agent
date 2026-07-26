from datetime import datetime, timezone
from uuid import uuid4

from backend.app.db.repositories import memory_repository
from backend.app.db.repositories.memory_repository import SqlMemoryRepository
from backend.app.schemas.memories import SqlMemoryRecord, SqlMemoryUpsert


class _Cursor:
    def __init__(self, row) -> None:
        self.row = row
        self.calls: list[tuple[str, tuple]] = []

    def execute(self, query: str, parameters: tuple) -> None:
        self.calls.append((query, parameters))

    def fetchone(self):
        return self.row


class _Connection:
    def __init__(self, cursor: _Cursor) -> None:
        self._cursor = cursor

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        return None

    def cursor(self) -> _Cursor:
        return self._cursor


def test_verified_memory_success_does_not_replace_reviewed_sql(monkeypatch) -> None:
    existing = SqlMemoryRecord(
        id=uuid4(),
        canonical_question="2017 年已支付订单数是多少？",
        normalized_question="查询2017年已支付订单数",
        sql_template="SELECT COUNT(*) FROM orders",
        final_sql="SELECT COUNT(*) AS order_count FROM orders",
        tables=["orders"],
        metrics=["order_count"],
        filters={"trust_status": "verified"},
        trust_status="verified",
        success_count=2,
        failure_count=0,
        avg_latency_ms=100,
        last_result_columns=["order_count"],
        last_row_count=1,
        created_at=datetime.now(timezone.utc),
    )
    cursor = _Cursor(_row(existing, success_count=3, avg_latency_ms=80))
    monkeypatch.setattr(memory_repository, "get_connection", lambda: _Connection(cursor))

    updated = SqlMemoryRepository()._update_success(
        existing,
        SqlMemoryUpsert(
            canonical_question=existing.canonical_question,
            sql_template="SELECT wrong_template",
            final_sql="SELECT wrong_sql",
            tables=["payments"],
            metrics=["sales_amount"],
            latency_ms=40,
        ),
    )

    query, parameters = cursor.calls[0]
    assert "final_sql" not in query.lower().split("returning", maxsplit=1)[0]
    assert parameters == (3, 80, str(existing.id))
    assert updated.trust_status == "verified"
    assert updated.final_sql == existing.final_sql


def _row(memory: SqlMemoryRecord, *, success_count: int, avg_latency_ms: int) -> tuple:
    return (
        memory.id,
        memory.canonical_question,
        memory.normalized_question,
        memory.question_pattern,
        memory.intent,
        memory.sql_template,
        memory.final_sql,
        memory.param_schema,
        memory.parameters,
        memory.tables,
        memory.metrics,
        memory.dimensions,
        memory.filters,
        memory.dialect,
        memory.schema_version,
        success_count,
        memory.failure_count,
        avg_latency_ms,
        memory.last_result_columns,
        memory.last_row_count,
        memory.last_used_at,
        memory.created_at,
    )
