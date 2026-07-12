from backend.app.schemas.retrieval import MetricContext, SchemaColumnContext
from backend.app.tools.context_reranker import detect_retrieval_intents, rerank_context


def test_detect_retrieval_intents_covers_metric_table_field_and_time() -> None:
    intents = detect_retrieval_intents("最近 30 天按城市看客单价趋势")

    assert "avg_order_value" in intents.metric_names
    assert "users" in intents.tables
    assert "city" in intents.fields
    assert intents.time is True


def test_rerank_context_promotes_required_time_dimension_and_diagnostics() -> None:
    metrics = [
        MetricContext(
            metric_name="avg_order_value",
            display_name="客单价",
            description="平均每笔订单金额",
            formula="SUM(orders.total_amount) / COUNT(DISTINCT orders.id)",
            required_tables=["orders", "users"],
            required_fields=["orders.total_amount", "orders.id", "orders.created_at", "users.city"],
            semantic_score=0.2,
            score=0.6,
        ),
        MetricContext(
            metric_name="refund_rate",
            display_name="退款率",
            description="退款订单占比",
            formula="COUNT(refunds.id) / COUNT(orders.id)",
            required_tables=["orders", "refunds"],
            required_fields=["orders.id", "refunds.id"],
            semantic_score=0.9,
            score=1.0,
        ),
    ]
    schema_columns = [
        _column("orders", "status", score=2.2),
        _column("refunds", "id", score=2.0),
        _column("orders", "total_amount", score=0.2),
        _column("orders", "created_at", data_type="timestamp", score=0.2),
        _column("users", "city", score=0.1),
        _column("orders", "id", score=0.1),
    ]

    reranked_metrics, reranked_columns, diagnostics = rerank_context(
        "最近 30 天按城市看客单价趋势",
        metrics,
        schema_columns,
        max_schema_columns=5,
    )

    fields = [f"{column.table_name}.{column.column_name}" for column in reranked_columns]
    assert reranked_metrics[0].metric_name == "avg_order_value"
    assert "orders.created_at" in fields
    assert "users.city" in fields
    assert "orders.total_amount" in fields
    assert diagnostics.compression == {"input": 6, "kept": 5, "max": 5}
    assert diagnostics.coverage["missing_required_fields"] == []
    assert "Rerank diagnostics" in diagnostics.summary_lines()[0]


def _column(
    table_name: str,
    column_name: str,
    *,
    data_type: str = "text",
    score: float = 0,
) -> SchemaColumnContext:
    return SchemaColumnContext(
        table_name=table_name,
        column_name=column_name,
        data_type=data_type,
        description=f"{table_name}.{column_name}",
        business_meaning=f"{table_name}.{column_name}",
        score=score,
    )
