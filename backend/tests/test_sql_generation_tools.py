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


def test_generate_or_rewrite_sales_sql_renders_top_product_sales() -> None:
    plan = plan_sql_reuse([])

    result = generate_or_rewrite_sales_sql("销售额最高的前 10 个商品是什么？", plan)

    assert result.parameters is not None
    assert result.parameters.metric == "top_product_sales"
    assert result.parameters.limit == 10
    assert "product_label" in result.sql
    assert "ORDER BY daily_sales DESC" in result.sql


def test_generate_or_rewrite_sales_sql_renders_refund_and_payment_rates() -> None:
    plan = plan_sql_reuse([])

    refund = generate_or_rewrite_sales_sql("哪个商品品类退款率最高？", plan)
    payment = generate_or_rewrite_sales_sql("每个支付方式的成功率是多少？", plan)

    assert refund.parameters is not None
    assert refund.parameters.metric == "category_refund_rate"
    assert "refund_rate" in refund.sql
    assert payment.parameters is not None
    assert payment.parameters.metric == "payment_success_rate"
    assert "success_rate" in payment.sql


def test_generate_or_rewrite_sales_sql_renders_gross_margin() -> None:
    plan = plan_sql_reuse([])

    result = generate_or_rewrite_sales_sql("最近 30 天毛利率最高的商品品类是什么？", plan)

    assert result.parameters is not None
    assert result.parameters.metric == "category_gross_margin"
    assert "gross_margin" in result.sql
    assert "product_costs" in result.sql


def test_generate_or_rewrite_sales_sql_renders_user_dimension_metrics() -> None:
    plan = plan_sql_reuse([])

    repeat = generate_or_rewrite_sales_sql("最近 90 天复购率是多少？", plan)
    city = generate_or_rewrite_sales_sql("每个城市的客单价是多少？", plan)

    assert repeat.parameters is not None
    assert repeat.parameters.metric == "repeat_purchase_rate"
    assert "repeat_rate" in repeat.sql
    assert city.parameters is not None
    assert city.parameters.metric == "city_avg_order_value"
    assert "city_label" in city.sql


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
