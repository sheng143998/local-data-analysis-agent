from datetime import datetime, timezone
from uuid import uuid4

from backend.app.core.embedding_adapter import EmbeddingResponse
from backend.app.schemas.memories import SqlMemoryRecord
from backend.app.tools.sql_memory_tools import (
    _build_sql_memory_embeddings,
    build_sql_memory_context_fingerprints,
    plan_sql_reuse,
    retrieve_sql_memory,
    upsert_successful_sql_memory,
)
from backend.app.schemas.retrieval import RetrievalContext, SchemaColumnContext


class FakeMemoryRepository:
    def __init__(self, memories: list[SqlMemoryRecord]) -> None:
        self.memories = memories
        self.upsert_payload = None

    def list(self, limit: int = 100) -> list[SqlMemoryRecord]:
        return self.memories[:limit]

    def upsert_success(self, payload):
        self.upsert_payload = payload
        return _memory(
            payload.canonical_question,
            final_sql=payload.final_sql,
            tables=payload.tables,
        )


class FakeEmbeddingAdapter:
    def __init__(self, ok: bool = True) -> None:
        self.ok = ok
        self.calls: list[list[str]] = []

    def embed(self, request):
        self.calls.append(request.texts)
        return EmbeddingResponse(
            ok=self.ok,
            vectors=[[0.1, 0.2], [0.3, 0.4]] if self.ok else [],
            provider="deterministic",
            model="test",
            dimension=2,
            latency_ms=1,
            error_message=None if self.ok else "embedding failed",
        )


def test_retrieve_sql_memory_scores_exact_sales_question() -> None:
    memory = _memory("最近 30 天销售额按天变化如何？", trust_status="verified")
    candidates = retrieve_sql_memory(
        "最近 30 天销售额按天变化如何？",
        metrics=["sales_amount", "order_count"],
        tables=["orders", "payments"],
        repository=FakeMemoryRepository([memory]),
    )

    assert len(candidates) == 1
    assert candidates[0].score >= 0.88
    assert candidates[0].memory.id == memory.id


def test_plan_sql_reuse_uses_fast_path_for_high_confidence_candidate() -> None:
    memory = _memory("最近 30 天销售额按天变化如何？", trust_status="verified")
    candidates = retrieve_sql_memory(
        "最近 30 天销售额按天变化如何？",
        metrics=["sales_amount", "order_count"],
        tables=["orders", "payments"],
        repository=FakeMemoryRepository([memory]),
    )
    plan = plan_sql_reuse(candidates)

    assert plan.path_type == "fast_path"
    assert plan.reuse_type == "parameter_rewrite"
    assert plan.memory_hit is True
    assert plan.selected_sql == memory.final_sql


def test_plan_sql_reuse_defaults_to_cold_path_without_candidates() -> None:
    plan = plan_sql_reuse([])

    assert plan.path_type == "cold_path"
    assert plan.memory_hit is False
    assert plan.candidate_count == 0


def test_plan_sql_reuse_blocks_fast_path_when_required_tables_missing() -> None:
    memory = _memory("过去 6 个月每月新增用户数是多少？")
    candidates = retrieve_sql_memory(
        "过去 6 个月每月新增用户数是多少？",
        metrics=["sales_amount"],
        tables=["users", "orders"],
        repository=FakeMemoryRepository([memory]),
    )
    plan = plan_sql_reuse(candidates)

    assert candidates[0].score >= 0.88
    assert candidates[0].required_tables == ["users"]
    assert candidates[0].required_table_match is False
    assert plan.path_type == "rewrite_path"
    assert plan.memory_hit is False


def test_plan_sql_reuse_allows_fast_path_when_required_tables_match() -> None:
    memory = _memory(
        "过去 6 个月每月新增用户数是多少？",
        final_sql="SELECT u.id FROM users u LIMIT 10",
        tables=["users"],
        trust_status="verified",
    )
    candidates = retrieve_sql_memory(
        "过去 6 个月每月新增用户数是多少？",
        metrics=["user_count"],
        tables=["users"],
        repository=FakeMemoryRepository([memory]),
    )
    plan = plan_sql_reuse(candidates)

    assert candidates[0].required_table_match is True
    assert plan.path_type == "fast_path"
    assert plan.memory_hit is True


def test_plan_sql_reuse_downgrades_verified_memory_when_context_fingerprint_is_missing() -> None:
    memory = _memory("最近 30 天销售额按天变化如何？", trust_status="verified")
    candidates = retrieve_sql_memory(
        "最近 30 天销售额按天变化如何？", metrics=["sales_amount"], tables=["orders", "payments"],
        repository=FakeMemoryRepository([memory]), context_fingerprints={"schema": "now", "semantic_contracts": "now"},
    )

    assert candidates[0].context_fingerprint_mismatches == ["schema", "semantic_contracts"]
    assert plan_sql_reuse(candidates).path_type == "rewrite_path"


def test_plan_sql_reuse_accepts_matching_context_fingerprints() -> None:
    fingerprints = {"schema": "schema-v1", "semantic_contracts": "contracts-v1"}
    memory = _memory("最近 30 天销售额按天变化如何？", trust_status="verified")
    memory = memory.model_copy(update={"filters": {"context_fingerprints": fingerprints}})
    candidates = retrieve_sql_memory(
        "最近 30 天销售额按天变化如何？", metrics=["sales_amount"], tables=["orders", "payments"],
        repository=FakeMemoryRepository([memory]), context_fingerprints=fingerprints,
    )

    assert candidates[0].context_fingerprint_match is True
    assert plan_sql_reuse(candidates).path_type == "fast_path"


def test_context_fingerprints_change_with_schema_or_contract_version() -> None:
    context = RetrievalContext(
        tables=["orders"], fields=["orders.id"],
        schema_columns=[SchemaColumnContext(
            table_name="orders", column_name="id", data_type="text",
            description="orders.id", business_meaning="订单标识",
        )],
    )
    first = build_sql_memory_context_fingerprints(context, [{"contract_key": "order_total", "version": 1}])
    second = build_sql_memory_context_fingerprints(context, [{"contract_key": "order_total", "version": 2}])
    changed_schema = context.model_copy(update={"fields": ["orders.id", "orders.created_at"]})

    assert first["semantic_contracts"] != second["semantic_contracts"]
    assert first["schema"] != build_sql_memory_context_fingerprints(changed_schema)["schema"]


def test_retrieve_sql_memory_uses_vector_semantic_score_when_available() -> None:
    close_text_memory = _memory("最近 30 天销售额按天变化如何？")
    semantic_memory = _memory(
        "经营表现看一下",
        final_sql="SELECT COUNT(*) FROM orders LIMIT 10",
    )
    candidates = retrieve_sql_memory(
        "最近 30 天销售额按天变化如何？",
        metrics=["sales_amount"],
        tables=["orders"],
        repository=FakeMemoryRepository([semantic_memory, close_text_memory]),
        semantic_scores={str(semantic_memory.id): 0.99, str(close_text_memory.id): 0.1},
    )

    assert candidates[0].memory.id == semantic_memory.id
    assert candidates[0].semantic_similarity == 0.99
    assert candidates[1].semantic_similarity == 0.1


def test_retrieve_sql_memory_falls_back_to_text_similarity_without_vector_score() -> None:
    memory = _memory("最近 30 天销售额按天变化如何？")
    candidates = retrieve_sql_memory(
        "最近 30 天销售额按天变化如何？",
        metrics=["sales_amount"],
        tables=["orders"],
        repository=FakeMemoryRepository([memory]),
        semantic_scores={},
    )

    assert candidates[0].semantic_similarity == candidates[0].text_similarity


def test_upsert_successful_sql_memory_passes_question_and_sql_embeddings() -> None:
    repo = FakeMemoryRepository([])

    upsert_successful_sql_memory(
        question="最近 30 天销售额是多少？",
        sql_template="SELECT 1",
        final_sql="SELECT 1 LIMIT 30",
        tables=["orders"],
        metrics=["sales_amount"],
        dimensions=["date"],
        result_columns=["daily_sales"],
        row_count=1,
        latency_ms=12,
        repository=repo,
        adapter=FakeEmbeddingAdapter(),
    )

    assert repo.upsert_payload is not None
    assert repo.upsert_payload.question_embedding == [0.1, 0.2]
    assert repo.upsert_payload.sql_embedding == [0.3, 0.4]
    assert repo.upsert_payload.dimensions == ["date"]
    assert repo.upsert_payload.trust_status == "executed"
    assert repo.upsert_payload.filters == {"context_fingerprints": {}}


def test_build_sql_memory_embeddings_returns_none_when_adapter_fails() -> None:
    question_embedding, sql_embedding = _build_sql_memory_embeddings(
        question="最近 30 天销售额是多少？",
        final_sql="SELECT 1",
        adapter=FakeEmbeddingAdapter(ok=False),
    )

    assert question_embedding is None
    assert sql_embedding is None


def _memory(
    question: str,
    *,
    final_sql: str = "SELECT DATE(created_at), SUM(total_amount) FROM orders GROUP BY 1 LIMIT 30",
    tables: list[str] | None = None,
    trust_status: str = "reviewed",
) -> SqlMemoryRecord:
    return SqlMemoryRecord(
        id=uuid4(),
        canonical_question=question,
        normalized_question=question.lower(),
        sql_template="SELECT DATE(created_at), SUM(total_amount) FROM orders GROUP BY 1",
        final_sql=final_sql,
        tables=tables or ["orders", "payments"],
        metrics=["sales_amount", "order_count"],
        trust_status=trust_status,
        success_count=5,
        failure_count=0,
        avg_latency_ms=20,
        last_result_columns=["order_date", "daily_sales"],
        last_row_count=30,
        created_at=datetime.now(timezone.utc),
    )
