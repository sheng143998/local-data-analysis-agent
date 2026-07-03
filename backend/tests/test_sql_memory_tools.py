from datetime import datetime, timezone
from uuid import uuid4

from backend.app.schemas.memories import SqlMemoryRecord
from backend.app.tools.sql_memory_tools import plan_sql_reuse, retrieve_sql_memory


class FakeMemoryRepository:
    def __init__(self, memories: list[SqlMemoryRecord]) -> None:
        self.memories = memories

    def list(self, limit: int = 100) -> list[SqlMemoryRecord]:
        return self.memories[:limit]


def test_retrieve_sql_memory_scores_exact_sales_question() -> None:
    memory = _memory("最近 30 天销售额按天变化如何？")
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
    memory = _memory("最近 30 天销售额按天变化如何？")
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


def _memory(question: str) -> SqlMemoryRecord:
    return SqlMemoryRecord(
        id=uuid4(),
        canonical_question=question,
        normalized_question=question.lower(),
        sql_template="SELECT DATE(created_at), SUM(total_amount) FROM orders GROUP BY 1",
        final_sql="SELECT DATE(created_at), SUM(total_amount) FROM orders GROUP BY 1 LIMIT 30",
        tables=["orders", "payments"],
        metrics=["sales_amount", "order_count"],
        success_count=5,
        failure_count=0,
        avg_latency_ms=20,
        last_result_columns=["order_date", "daily_sales"],
        last_row_count=30,
        created_at=datetime.now(timezone.utc),
    )
