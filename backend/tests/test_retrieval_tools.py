from backend.app.schemas.retrieval import SchemaColumnContext
from backend.app.tools.context_builder import build_retrieval_context, infer_table_relationships
from backend.app.tools.metric_retriever import retrieve_metrics
from backend.app.tools.schema_retriever import retrieve_schema


def test_metric_retriever_finds_sales_context() -> None:
    metrics = retrieve_metrics("最近 30 天销售额按天变化如何？")

    metric_names = {metric.metric_name for metric in metrics}
    assert "sales_amount" in metric_names
    assert any("orders" in metric.required_tables for metric in metrics)
    assert any("payments" in metric.required_tables for metric in metrics)
    assert all(metric.score > 0 for metric in metrics)


def test_schema_retriever_returns_required_columns() -> None:
    metrics = retrieve_metrics("最近 30 天销售额按天变化如何？")
    columns = retrieve_schema("最近 30 天销售额按天变化如何？", metrics)

    fields = {f"{column.table_name}.{column.column_name}" for column in columns}
    assert "orders.created_at" in fields
    assert "orders.total_amount" in fields
    assert "orders.status" in fields
    required = {
        f"{column.table_name}.{column.column_name}": column.score
        for column in columns
        if f"{column.table_name}.{column.column_name}" in fields
    }
    assert required["orders.total_amount"] > 0


def test_schema_retriever_prioritizes_refund_context() -> None:
    metrics = retrieve_metrics("哪个商品品类退款率最高？")
    columns = retrieve_schema("哪个商品品类退款率最高？", metrics)

    fields = {f"{column.table_name}.{column.column_name}" for column in columns}
    assert "refunds.order_id" in fields
    assert "products.category" in fields
    assert any(column.score > 0 for column in columns)


def test_context_builder_combines_metrics_and_schema() -> None:
    context = build_retrieval_context("最近 30 天销售额按天变化如何？")

    assert "orders" in context.tables
    assert "payments" in context.tables
    assert "orders.total_amount" in context.fields
    assert any(
        relationship.left_table == "orders"
        and relationship.left_column == "id"
        and relationship.right_table == "payments"
        and relationship.right_column == "order_id"
        for relationship in context.table_relationships
    )
    assert "销售额" in context.metric_summary


def test_infer_table_relationships_from_generic_id_conventions() -> None:
    relationships = infer_table_relationships(
        [
            _column("orders", "id"),
            _column("orders", "user_id"),
            _column("payments", "order_id"),
            _column("coupon_usages", "order_id"),
            _column("users", "id"),
        ]
    )

    pairs = {
        (
            relationship.left_table,
            relationship.left_column,
            relationship.right_table,
            relationship.right_column,
            relationship.relationship_type,
        )
        for relationship in relationships
    }

    assert ("orders", "id", "payments", "order_id", "id_to_foreign_key") in pairs
    assert ("orders", "id", "coupon_usages", "order_id", "id_to_foreign_key") in pairs
    assert ("users", "id", "orders", "user_id", "id_to_foreign_key") in pairs
    assert any(
        relationship.left_column == "order_id"
        and relationship.right_column == "order_id"
        and relationship.relationship_type == "same_key"
        for relationship in relationships
    )


def _column(table_name: str, column_name: str) -> SchemaColumnContext:
    return SchemaColumnContext(
        table_name=table_name,
        column_name=column_name,
        data_type="text",
        description=f"{table_name}.{column_name}",
        business_meaning=f"{table_name}.{column_name}",
    )
