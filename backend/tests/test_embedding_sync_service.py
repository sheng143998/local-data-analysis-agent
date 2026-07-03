from __future__ import annotations

from contextlib import contextmanager
from typing import Any

from backend.app.core.embedding_adapter import EmbeddingResponse
from backend.app.services import embedding_sync_service
from backend.app.services.embedding_sync_service import (
    EmbeddingSyncService,
    MetricEmbeddingRecord,
    SchemaEmbeddingRecord,
    SqlMemoryEmbeddingRecord,
    _json_object,
    _batch_size_value,
    _limit_params,
    _sleep_seconds,
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
        text = "\n".join(request.texts)
        self.calls.extend(request.texts)
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
            vectors=[
                self.vectors[min(index, len(self.vectors) - 1)]
                for index, _ in enumerate(request.texts)
            ],
            provider="deterministic",
            model="test",
            dimension=3,
            latency_ms=1,
        )


class MultiTextFakeAdapter:
    def __init__(self, fail: bool = False, short_response: bool = False) -> None:
        self.fail = fail
        self.short_response = short_response
        self.calls: list[list[str]] = []

    def embed(self, request):
        self.calls.append(request.texts)
        if self.fail:
            return EmbeddingResponse(
                ok=False,
                provider="deterministic",
                model="test",
                dimension=2,
                latency_ms=1,
                error_message="boom",
            )
        vectors = [[0.1, 0.2], [0.3, 0.4], [0.5, 0.6], [0.7, 0.8]]
        if self.short_response:
            vectors = vectors[:1]
        return EmbeddingResponse(
            ok=True,
            vectors=vectors[: len(request.texts)],
            provider="deterministic",
            model="test",
            dimension=2,
            latency_ms=1,
        )


class BatchThenSingleFakeAdapter:
    def __init__(self, fail_single_text: str | None = None) -> None:
        self.fail_single_text = fail_single_text
        self.calls: list[list[str]] = []

    def embed(self, request):
        self.calls.append(request.texts)
        if len(request.texts) > 1:
            return EmbeddingResponse(
                ok=False,
                provider="deterministic",
                model="test",
                dimension=2,
                latency_ms=1,
                error_message="batch failed",
            )
        if self.fail_single_text and self.fail_single_text in request.texts[0]:
            return EmbeddingResponse(
                ok=False,
                provider="deterministic",
                model="test",
                dimension=2,
                latency_ms=1,
                error_message="single failed",
            )
        return EmbeddingResponse(
            ok=True,
            vectors=[[0.9, 0.8]],
            provider="deterministic",
            model="test",
            dimension=2,
            latency_ms=1,
        )


class MemoryBatchThenSingleFakeAdapter:
    def __init__(self, fail_memory_question: str | None = None) -> None:
        self.fail_memory_question = fail_memory_question
        self.calls: list[list[str]] = []

    def embed(self, request):
        self.calls.append(request.texts)
        if len(request.texts) > 2:
            return EmbeddingResponse(
                ok=False,
                provider="deterministic",
                model="test",
                dimension=2,
                latency_ms=1,
                error_message="batch failed",
            )
        if self.fail_memory_question and request.texts and self.fail_memory_question in request.texts[0]:
            return EmbeddingResponse(
                ok=False,
                provider="deterministic",
                model="test",
                dimension=2,
                latency_ms=1,
                error_message="single failed",
            )
        return EmbeddingResponse(
            ok=True,
            vectors=[[0.9, 0.8], [0.7, 0.6]],
            provider="deterministic",
            model="test",
            dimension=2,
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


def _fake_sleeper(calls: list[float]):
    def sleep_call(seconds: float) -> None:
        calls.append(seconds)

    return sleep_call


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


def test_limit_params_accepts_empty_and_positive_values() -> None:
    assert _limit_params(None) is None
    assert _limit_params(2) == (2,)


def test_limit_params_rejects_non_positive_values() -> None:
    import pytest

    with pytest.raises(ValueError, match="limit must be greater than 0"):
        _limit_params(0)


def test_batch_size_value_accepts_positive_values() -> None:
    assert _batch_size_value(2) == 2


def test_batch_size_value_rejects_non_positive_values() -> None:
    import pytest

    with pytest.raises(ValueError, match="batch_size must be greater than 0"):
        _batch_size_value(0)


def test_sleep_seconds_accepts_zero_and_positive_values() -> None:
    assert _sleep_seconds(0) == 0
    assert _sleep_seconds(250) == 0.25


def test_sleep_seconds_rejects_negative_values() -> None:
    import pytest

    with pytest.raises(ValueError, match="sleep_ms must be greater than or equal to 0"):
        _sleep_seconds(-1)


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


def test_sync_schema_embeddings_batches_documents(monkeypatch) -> None:
    cursor = FakeCursor(
        rows=[
            ("orders", "total_amount", "numeric", "订单金额", "销售额分析"),
            ("orders", "created_at", "timestamp", "下单时间", "时间分析"),
            ("users", "city", "text", "城市", "地域分析"),
        ]
    )
    adapter = FakeAdapter(vectors=[[0.1], [0.2]])
    _patch_connection(monkeypatch, cursor)

    result = EmbeddingSyncService(adapter=adapter).sync_schema_embeddings(batch_size=2)

    assert result.scanned == 3
    assert result.updated == 3
    assert len(adapter.calls) == 3
    update_calls = [call for call in cursor.executed if "UPDATE schema_metadata" in call[0]]
    assert [call[1][0] for call in update_calls] == ["[0.10000000]", "[0.20000000]", "[0.10000000]"]


def test_sync_schema_embeddings_sleeps_between_batches(monkeypatch) -> None:
    cursor = FakeCursor(
        rows=[
            ("orders", "total_amount", "numeric", "订单金额", "销售额分析"),
            ("orders", "created_at", "timestamp", "下单时间", "时间分析"),
            ("users", "city", "text", "城市", "地域分析"),
        ]
    )
    sleep_calls: list[float] = []
    _patch_connection(monkeypatch, cursor)

    result = EmbeddingSyncService(
        adapter=FakeAdapter(vectors=[[0.1]]),
        sleeper=_fake_sleeper(sleep_calls),
    ).sync_schema_embeddings(batch_size=1, sleep_ms=100)

    assert result.updated == 3
    assert sleep_calls == [0.1, 0.1]


def test_sync_schema_embeddings_applies_limit_to_select(monkeypatch) -> None:
    cursor = FakeCursor(rows=[("orders", "total_amount", "numeric", "订单金额", "销售额分析")])
    _patch_connection(monkeypatch, cursor)

    result = EmbeddingSyncService(adapter=FakeAdapter(vectors=[[0.1]])).sync_schema_embeddings(limit=1)

    select_sql, select_params = cursor.executed[0]
    assert result.scanned == 1
    assert "LIMIT %s" in select_sql
    assert select_params == (1,)


def test_sync_schema_embeddings_marks_whole_batch_failed_when_retry_disabled(monkeypatch) -> None:
    cursor = FakeCursor(
        rows=[
            ("orders", "total_amount", "numeric", "订单金额", "销售额分析"),
            ("orders", "created_at", "timestamp", "下单时间", "时间分析"),
        ]
    )
    _patch_connection(monkeypatch, cursor)

    result = EmbeddingSyncService(adapter=MultiTextFakeAdapter(short_response=True)).sync_schema_embeddings(
        batch_size=2,
        retry_single_on_batch_failure=False,
    )

    assert result.scanned == 2
    assert result.updated == 0
    assert result.failed == 2
    assert len(result.errors) == 2
    assert not [call for call in cursor.executed if "UPDATE schema_metadata" in call[0]]


def test_sync_schema_embeddings_retries_single_records_after_batch_failure(monkeypatch) -> None:
    cursor = FakeCursor(
        rows=[
            ("orders", "bad_column", "text", "会失败", ""),
            ("orders", "ok_column", "text", "可同步", ""),
        ]
    )
    adapter = BatchThenSingleFakeAdapter(fail_single_text="bad_column")
    _patch_connection(monkeypatch, cursor)

    result = EmbeddingSyncService(adapter=adapter).sync_schema_embeddings(batch_size=2)

    assert result.scanned == 2
    assert result.updated == 1
    assert result.failed == 1
    assert result.errors == ["schema:orders.bad_column: single failed"]
    assert len(adapter.calls) == 3
    update_calls = [call for call in cursor.executed if "UPDATE schema_metadata" in call[0]]
    assert update_calls[0][1] == ("[0.90000000,0.80000000]", "orders", "ok_column")


def test_sync_schema_embeddings_sleeps_during_single_retry(monkeypatch) -> None:
    cursor = FakeCursor(
        rows=[
            ("orders", "bad_column", "text", "会失败", ""),
            ("orders", "ok_column", "text", "可同步", ""),
        ]
    )
    sleep_calls: list[float] = []
    _patch_connection(monkeypatch, cursor)

    result = EmbeddingSyncService(
        adapter=BatchThenSingleFakeAdapter(fail_single_text="bad_column"),
        sleeper=_fake_sleeper(sleep_calls),
    ).sync_schema_embeddings(batch_size=2, sleep_ms=50)

    assert result.updated == 1
    assert result.failed == 1
    assert sleep_calls == [0.05, 0.05]


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


def test_sync_metric_embeddings_applies_limit_to_select(monkeypatch) -> None:
    cursor = FakeCursor(
        rows=[
            (
                "m1",
                "sales_amount",
                "销售额",
                "已支付订单金额",
                "sum(amount)",
                ["orders"],
                ["orders.total_amount"],
                "{}",
            )
        ]
    )
    _patch_connection(monkeypatch, cursor)

    EmbeddingSyncService(adapter=FakeAdapter(vectors=[[0.4]])).sync_metric_embeddings(limit=3)

    select_sql, select_params = cursor.executed[0]
    assert "LIMIT %s" in select_sql
    assert select_params == (3,)


def test_sync_metric_embeddings_batches_documents(monkeypatch) -> None:
    cursor = FakeCursor(
        rows=[
            ("m1", "sales_amount", "销售额", "金额", "sum(amount)", ["orders"], ["orders.total_amount"], "{}"),
            ("m2", "order_count", "订单数", "订单", "count(*)", ["orders"], ["orders.id"], "{}"),
        ]
    )
    adapter = FakeAdapter(vectors=[[0.4], [0.5]])
    _patch_connection(monkeypatch, cursor)

    result = EmbeddingSyncService(adapter=adapter).sync_metric_embeddings(batch_size=2)

    assert result.updated == 2
    update_calls = [call for call in cursor.executed if "UPDATE metric_definitions" in call[0]]
    assert [call[1] for call in update_calls] == [("[0.40000000]", "m1"), ("[0.50000000]", "m2")]


def test_sync_metric_embeddings_retries_single_records_after_batch_failure(monkeypatch) -> None:
    cursor = FakeCursor(
        rows=[
            ("m1", "bad_metric", "坏指标", "会失败", "bad()", ["orders"], ["orders.id"], "{}"),
            ("m2", "order_count", "订单数", "订单", "count(*)", ["orders"], ["orders.id"], "{}"),
        ]
    )
    adapter = BatchThenSingleFakeAdapter(fail_single_text="bad_metric")
    _patch_connection(monkeypatch, cursor)

    result = EmbeddingSyncService(adapter=adapter).sync_metric_embeddings(batch_size=2)

    assert result.updated == 1
    assert result.failed == 1
    assert result.errors == ["metric:bad_metric: single failed"]
    update_calls = [call for call in cursor.executed if "UPDATE metric_definitions" in call[0]]
    assert update_calls[0][1] == ("[0.90000000,0.80000000]", "m2")


def test_sync_records_embedding_failures_without_stopping(monkeypatch) -> None:
    cursor = FakeCursor(
        rows=[
            ("orders", "bad_column", "text", "会失败", ""),
            ("orders", "ok_column", "text", "可同步", ""),
        ]
    )
    _patch_connection(monkeypatch, cursor)

    result = EmbeddingSyncService(adapter=FakeAdapter(fail_on="bad_column")).sync_schema_embeddings(batch_size=1)

    assert result.scanned == 2
    assert result.updated == 1
    assert result.failed == 1
    assert result.errors == ["schema:orders.bad_column: boom"]


def test_sync_sql_memory_embeddings_updates_question_and_sql_vectors(monkeypatch) -> None:
    cursor = FakeCursor(
        rows=[
            ("mem-1", "最近 30 天销售额是多少？", "SELECT SUM(total_amount) FROM orders"),
        ]
    )
    adapter = MultiTextFakeAdapter()
    _patch_connection(monkeypatch, cursor)

    result = EmbeddingSyncService(adapter=adapter).sync_sql_memory_embeddings()

    assert result.target == "memory"
    assert result.scanned == 1
    assert result.updated == 1
    assert result.failed == 0
    assert adapter.calls == [["最近 30 天销售额是多少？", "SELECT SUM(total_amount) FROM orders"]]
    select_sql, select_params = cursor.executed[0]
    assert "FROM sql_memories" in select_sql
    assert "question_embedding IS NULL OR sql_embedding IS NULL" in select_sql
    assert select_params is None
    update_calls = [call for call in cursor.executed if "UPDATE sql_memories" in call[0]]
    assert update_calls[0][1] == ("[0.10000000,0.20000000]", "[0.30000000,0.40000000]", "mem-1")


def test_sync_sql_memory_embeddings_batches_question_sql_pairs(monkeypatch) -> None:
    cursor = FakeCursor(
        rows=[
            ("mem-1", "问题一", "SELECT 1"),
            ("mem-2", "问题二", "SELECT 2"),
        ]
    )
    adapter = MultiTextFakeAdapter()
    _patch_connection(monkeypatch, cursor)

    result = EmbeddingSyncService(adapter=adapter).sync_sql_memory_embeddings(batch_size=2)

    assert result.updated == 2
    assert adapter.calls == [["问题一", "SELECT 1", "问题二", "SELECT 2"]]
    update_calls = [call for call in cursor.executed if "UPDATE sql_memories" in call[0]]
    assert update_calls[0][1] == ("[0.10000000,0.20000000]", "[0.30000000,0.40000000]", "mem-1")
    assert update_calls[1][1] == ("[0.50000000,0.60000000]", "[0.70000000,0.80000000]", "mem-2")


def test_sync_sql_memory_embeddings_retries_single_records_after_batch_failure(monkeypatch) -> None:
    cursor = FakeCursor(
        rows=[
            ("mem-1", "坏问题", "SELECT bad"),
            ("mem-2", "好问题", "SELECT 2"),
        ]
    )
    adapter = MemoryBatchThenSingleFakeAdapter(fail_memory_question="坏问题")
    _patch_connection(monkeypatch, cursor)

    result = EmbeddingSyncService(adapter=adapter).sync_sql_memory_embeddings(batch_size=2)

    assert result.updated == 1
    assert result.failed == 1
    assert result.errors == ["memory:mem-1: single failed"]
    assert adapter.calls == [
        ["坏问题", "SELECT bad", "好问题", "SELECT 2"],
        ["坏问题", "SELECT bad"],
        ["好问题", "SELECT 2"],
    ]
    update_calls = [call for call in cursor.executed if "UPDATE sql_memories" in call[0]]
    assert update_calls[0][1] == ("[0.90000000,0.80000000]", "[0.70000000,0.60000000]", "mem-2")


def test_sync_sql_memory_embeddings_applies_limit_to_select(monkeypatch) -> None:
    cursor = FakeCursor(rows=[("mem-1", "问题", "SELECT 1")])
    _patch_connection(monkeypatch, cursor)

    EmbeddingSyncService(adapter=MultiTextFakeAdapter()).sync_sql_memory_embeddings(limit=5)

    select_sql, select_params = cursor.executed[0]
    assert "LIMIT %s" in select_sql
    assert select_params == (5,)


def test_sync_sql_memory_embeddings_records_failures(monkeypatch) -> None:
    cursor = FakeCursor(rows=[("mem-1", "问题", "SELECT 1")])
    _patch_connection(monkeypatch, cursor)

    result = EmbeddingSyncService(adapter=MultiTextFakeAdapter(fail=True)).sync_sql_memory_embeddings()

    assert result.scanned == 1
    assert result.updated == 0
    assert result.failed == 1
    assert result.errors == ["memory:mem-1: boom"]
    assert not [call for call in cursor.executed if "UPDATE sql_memories" in call[0]]


def test_load_sql_memory_records_maps_rows() -> None:
    cursor = FakeCursor(rows=[("mem-1", "问题", "SELECT 1")])

    records = EmbeddingSyncService(adapter=MultiTextFakeAdapter())._load_sql_memory_records(cursor)

    assert records == [
        SqlMemoryEmbeddingRecord(
            id="mem-1",
            canonical_question="问题",
            final_sql="SELECT 1",
        )
    ]
