from datetime import datetime, timezone
from uuid import uuid4

from backend.app.schemas.memories import SqlMemoryCandidate, SqlMemoryRecord
from backend.app.tools.sql_generation_tools import generate_or_rewrite_sales_sql
from backend.app.tools.sql_memory_tools import plan_sql_reuse


def test_generate_or_rewrite_sales_sql_rewrites_monthly_order_count() -> None:
    plan = plan_sql_reuse(
        [
            SqlMemoryCandidate(
                memory=_memory(),
                score=0.75,
                semantic_similarity=0.7,
                text_similarity=0.7,
                metric_table_match=0.9,
                success_score=1,
            )
        ]
    )

    result = generate_or_rewrite_sales_sql("最近 90 天每月订单数是多少？", plan)

    assert plan.path_type == "rewrite_path"
    assert result.path == "deterministic_rewrite"
    assert result.parameters is not None
    assert result.parameters.granularity == "month"
    assert result.parameters.metric == "order_count"
    assert "DATE_TRUNC('month', o.created_at)::date" in result.sql
    assert "LIMIT 3" in result.sql


def test_generate_or_rewrite_sales_sql_renders_cold_path_template() -> None:
    plan = plan_sql_reuse([])

    result = generate_or_rewrite_sales_sql("最近 7 天销售额是多少？", plan)

    assert result.path == "template_render"
    assert result.parameters is not None
    assert result.parameters.days == 7
    assert "LIMIT 7" in result.sql


def _memory() -> SqlMemoryRecord:
    return SqlMemoryRecord(
        id=uuid4(),
        canonical_question="最近 30 天销售额按天变化如何？",
        normalized_question="最近 30 天销售额按天变化如何？".lower(),
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
