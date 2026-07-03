from __future__ import annotations

from contextlib import contextmanager
from typing import Any

from backend.app.core.embedding_adapter import EmbeddingResponse
from backend.app.tools import vector_retrieval
from backend.app.tools.vector_retrieval import (
    _semantic_score,
    _vector_literal,
    retrieve_metric_vector_candidates,
    retrieve_schema_vector_candidates,
)


class FakeAdapter:
    def __init__(self, ok: bool = True) -> None:
        self.ok = ok
        self.calls: list[str] = []

    def embed(self, request):
        self.calls.append(request.texts[0])
        return EmbeddingResponse(
            ok=self.ok,
            vectors=[[0.1, 0.2]] if self.ok else [],
            provider="deterministic",
            model="test",
            dimension=2,
            latency_ms=1,
            error_message=None if self.ok else "embedding unavailable",
        )


class FakeCursor:
    def __init__(self, rows: list[tuple[str, float]]) -> None:
        self.rows = rows
        self.executed: list[tuple[str, tuple[Any, ...]]] = []

    def execute(self, sql: str, params: tuple[Any, ...]) -> None:
        self.executed.append((sql, params))

    def fetchall(self) -> list[tuple[str, float]]:
        return self.rows


class FakeConnection:
    def __init__(self, cursor: FakeCursor) -> None:
        self._cursor = cursor

    def cursor(self) -> FakeCursor:
        return self._cursor


def _patch_connection(monkeypatch, cursor: FakeCursor) -> None:
    @contextmanager
    def fake_get_connection():
        yield FakeConnection(cursor)

    monkeypatch.setattr(vector_retrieval, "get_connection", fake_get_connection)


def test_vector_literal_formats_pgvector_query_value() -> None:
    assert _vector_literal([0.1, -0.25]) == "[0.10000000,-0.25000000]"


def test_semantic_score_converts_cosine_distance_to_score() -> None:
    assert _semantic_score(0.2) == 0.8
    assert _semantic_score(-0.5) == 1.0
    assert _semantic_score(1.5) == 0.0
    assert _semantic_score("bad") == 0


def test_retrieve_metric_vector_candidates_queries_pgvector(monkeypatch) -> None:
    cursor = FakeCursor(rows=[("sales_amount", 0.12), ("refund_rate", 0.4)])
    _patch_connection(monkeypatch, cursor)

    candidates = retrieve_metric_vector_candidates("销售表现如何？", adapter=FakeAdapter())

    assert candidates == {"sales_amount": 0.88, "refund_rate": 0.6}
    sql, params = cursor.executed[0]
    assert "metric_definitions" in sql
    assert "embedding <=> %s::vector" in sql
    assert params == ("[0.10000000,0.20000000]", "[0.10000000,0.20000000]", 8)


def test_retrieve_schema_vector_candidates_can_filter_tables(monkeypatch) -> None:
    cursor = FakeCursor(rows=[("orders.total_amount", 0.1)])
    _patch_connection(monkeypatch, cursor)

    candidates = retrieve_schema_vector_candidates(
        "订单收入",
        tables=["orders"],
        limit=5,
        adapter=FakeAdapter(),
    )

    assert candidates == {"orders.total_amount": 0.9}
    sql, params = cursor.executed[0]
    assert "schema_metadata" in sql
    assert "table_name = ANY" in sql
    assert params == ("[0.10000000,0.20000000]", ["orders"], "[0.10000000,0.20000000]", 5)


def test_vector_candidates_fallback_to_empty_when_embedding_fails(monkeypatch) -> None:
    cursor = FakeCursor(rows=[("sales_amount", 0.12)])
    _patch_connection(monkeypatch, cursor)

    candidates = retrieve_metric_vector_candidates("销售表现如何？", adapter=FakeAdapter(ok=False))

    assert candidates == {}
    assert cursor.executed == []
