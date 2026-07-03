from __future__ import annotations

from contextlib import contextmanager
from typing import Any

from backend.app.core.embedding_adapter import EmbeddingResponse
from backend.app.services import embedding_sync_service
from backend.app.services.embedding_sync_service import (
    EmbeddingSyncService,
    MetricEmbeddingRecord,
    SchemaEmbeddingRecord,
    _json_object,
    _vector_literal,
    build_metric_embedding_document,
    build_schema_embedding_document,
)


class FakeAdapter:
    def __init__(self, vectors: list[list[float]] | None = None, fail_on: str | None = None) -> None:
        self.vectors = vectors or [[0.1, 0.2, 0.3]]
        self.fail_on = fail_on
        self.calls: list[str] = []

    def embed(self, request):
        text = request.texts[0]
        self.calls.append(text)
        if self.fail_on and self.fail_on in text:
            return EmbeddingResponse(
                ok=False,
                provider="deterministic",
                model="test",
                dimension=3,
                latency_ms=1,
                error_message="boom",
            )
        return EmbeddingResponse(
            ok=True,
            vectors=[self.vectors[min(len(self.calls) - 1, len(self.vectors) - 1)]],
            provider="deterministic",
            model="test",
            dimension=3,
            latency_ms=1,
        )


class FakeCursor:
    def __init__(self, rows: list[tuple[Any, ...]]) -> None:
        self.rows = rows
        self.executed: list[tuple[str, tuple[Any, ...] | None]] = []

    def execute(self, sql: str, params: tuple[Any, ...] | None = None) -> None:
        self.executed.append((sql, params))

    def fetchall(self) -> list[tuple[Any, ...]]:
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

    monkeypatch.setattr(embedding_sync_service, "get_connection", fake_get_connection)


def test_build_schema_embedding_document_contains_business_context() -> None:
    document = build_schema_embedding_document(
        SchemaEmbeddingRecord(
            table_name="orders",
            column_name="total_amount",
            data_type="numeric",
            description="订单实付金额",
            business_meaning="用于销售额分析",
        )
    )

    assert "表名: orders" in document
    assert "字段名: total_amount" in document
    assert "业务含义: 用于销售额分析" in document


def test_build_metric_embedding_document_contains_formula_and_dependencies() -> None:
    document = build_metric_embedding_document(
        MetricEmbeddingRecord(
            id="m1",
            metric_name="gross_margin",
            display_name="毛利率",
            description="销售毛利占销售额比例",
            formula="(sales - cost) / sales",
            required_tables=["order_items", "product_costs"],
            required_fields=["price", "unit_cost"],
            default_filters={"payment_status": "paid"},
        )
    )

    assert "指标名称: 毛利率" in document
    assert "计算公式: (sales - cost) / sales" in document
    assert "order_items, product_costs" in document
    assert '"payment_status": "paid"' in document


def test_vector_literal_formats_pgvector_value() -> None:
    assert _vector_literal([0.1, 1, -0.333333333]) == "[0.10000000,1.00000000,-0.33333333]"


def test_json_object_accepts_dict_json_string_and_invalid_values() -> None:
    assert _json_object({"a": 1}) == {"a": 1}
    assert _json_object('{"a": 1}') == {"a": 1}
    assert _json_object("[1, 2]") == {}
    assert _json_object("not-json") == {}
    assert _json_object(None) == {}


def test_sync_schema_embeddings_updates_pgvector(monkeypatch) -> None:
    cursor = FakeCursor(
        rows=[
            ("orders", "total_amount", "numeric", "订单金额", "销售额分析"),
            ("orders", "created_at", "timestamp", None, None),
        ]
    )
    _patch_connection(monkeypatch, cursor)

    result = EmbeddingSyncService(adapter=FakeAdapter(vectors=[[0.1], [0.2]])).sync_schema_embeddings()

    assert result.scanned == 2
    assert result.updated == 2
    assert result.failed == 0
    update_calls = [call for call in cursor.executed if "UPDATE schema_metadata" in call[0]]
    assert len(update_calls) == 2
    assert "%s::vector" in update_calls[0][0]
    assert update_calls[0][1] == ("[0.10000000]", "orders", "total_amount")


def test_sync_metric_embeddings_updates_pgvector(monkeypatch) -> None:
    cursor = FakeCursor(
        rows=[
            (
                "m1",
                "sales_amount",
                "销售额",
                "已支付订单金额",
                "sum(amount)",
                ["orders", "payments"],
                ["orders.id", "payments.amount"],
                '{"status":"paid"}',
            )
        ]
    )
    _patch_connection(monkeypatch, cursor)

    result = EmbeddingSyncService(adapter=FakeAdapter(vectors=[[0.4, 0.5]])).sync_metric_embeddings()

    assert result.scanned == 1
    assert result.updated == 1
    update_calls = [call for call in cursor.executed if "UPDATE metric_definitions" in call[0]]
    assert update_calls[0][1] == ("[0.40000000,0.50000000]", "m1")


def test_sync_records_embedding_failures_without_stopping(monkeypatch) -> None:
    cursor = FakeCursor(
        rows=[
            ("orders", "bad_column", "text", "会失败", ""),
            ("orders", "ok_column", "text", "可同步", ""),
        ]
    )
    _patch_connection(monkeypatch, cursor)

    result = EmbeddingSyncService(adapter=FakeAdapter(fail_on="bad_column")).sync_schema_embeddings()

    assert result.scanned == 2
    assert result.updated == 1
    assert result.failed == 1
    assert result.errors == ["schema:orders.bad_column: boom"]
