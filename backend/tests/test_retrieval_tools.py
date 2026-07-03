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


def test_schema_retriever_recalls_traffic_context() -> None:
    metrics = retrieve_metrics("按流量来源统计访问到下单的转化率")
    columns = retrieve_schema("按流量来源统计访问到下单的转化率", metrics)

    fields = {f"{column.table_name}.{column.column_name}" for column in columns}
    assert any(field.startswith("traffic_events.") for field in fields)
    assert "traffic_events.user_id" in fields
    assert "orders.user_id" in fields


def test_schema_retriever_recalls_coupon_context() -> None:
    metrics = retrieve_metrics("哪些优惠券核销率最高？")
    columns = retrieve_schema("哪些优惠券核销率最高？", metrics)

    fields = {f"{column.table_name}.{column.column_name}" for column in columns}
    assert "coupons.id" in fields
    assert "coupon_usages.coupon_id" in fields
    assert "coupon_usages.order_id" in fields


def test_schema_retriever_recalls_new_user_context() -> None:
    metrics = retrieve_metrics("过去 6 个月每月新增用户数是多少？")
    columns = retrieve_schema("过去 6 个月每月新增用户数是多少？", metrics)

    fields = {f"{column.table_name}.{column.column_name}" for column in columns}
    assert "users.id" in fields
    assert "users.created_at" in fields


def test_schema_retriever_recalls_top_user_context() -> None:
    metrics = retrieve_metrics("购买次数最多的前 10 个用户是谁？")
    columns = retrieve_schema("购买次数最多的前 10 个用户是谁？", metrics)

    fields = {f"{column.table_name}.{column.column_name}" for column in columns}
    assert "users.id" in fields
    assert "orders.user_id" in fields


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


def test_infer_table_relationships_prefers_postgres_foreign_keys(monkeypatch) -> None:
    def fake_loader(fields_by_table):
        assert fields_by_table["orders"] == {"id"}
        return [
            _relationship(
                "orders",
                "id",
                "payments",
                "order_id",
                "foreign_key",
                0.98,
                "PostgreSQL 外键约束 payments_order_id_fkey",
            )
        ]

    monkeypatch.setattr(
        "backend.app.tools.context_builder._load_postgres_foreign_key_relationships",
        fake_loader,
    )

    relationships = infer_table_relationships(
        [
            _column("orders", "id"),
            _column("payments", "order_id"),
        ],
        include_database_foreign_keys=True,
    )

    assert len(relationships) == 1
    assert relationships[0].relationship_type == "foreign_key"
    assert relationships[0].confidence == 0.98
    assert "PostgreSQL 外键约束" in relationships[0].reason


def test_infer_table_relationships_falls_back_when_postgres_foreign_keys_fail(
    monkeypatch,
) -> None:
    def fake_loader(fields_by_table):
        raise RuntimeError("database metadata unavailable")

    monkeypatch.setattr(
        "backend.app.tools.context_builder._load_postgres_foreign_key_relationships",
        fake_loader,
    )

    relationships = infer_table_relationships(
        [
            _column("orders", "id"),
            _column("payments", "order_id"),
        ],
        include_database_foreign_keys=True,
    )

    assert any(
        relationship.left_table == "orders"
        and relationship.right_table == "payments"
        and relationship.relationship_type == "id_to_foreign_key"
        for relationship in relationships
    )


def test_load_postgres_foreign_key_relationships_keeps_only_recalled_fields(
    monkeypatch,
) -> None:
    class FakeCursor:
        def execute(self, sql):
            assert "information_schema.table_constraints" in sql

        def fetchall(self):
            return [
                ("orders", "id", "payments", "order_id", "payments_order_id_fkey"),
                ("products", "id", "order_items", "product_id", "items_product_id_fkey"),
            ]

    class FakeConnection:
        def cursor(self):
            return FakeCursor()

    class FakeConnectionContext:
        def __enter__(self):
            return FakeConnection()

        def __exit__(self, exc_type, exc, traceback):
            return False

    monkeypatch.setattr(
        "backend.app.tools.context_builder.get_connection",
        lambda: FakeConnectionContext(),
    )

    from backend.app.tools.context_builder import _load_postgres_foreign_key_relationships

    relationships = _load_postgres_foreign_key_relationships(
        {
            "orders": {"id"},
            "payments": {"order_id"},
            "products": {"id"},
        }
    )

    assert [
        (
            relationship.left_table,
            relationship.left_column,
            relationship.right_table,
            relationship.right_column,
            relationship.relationship_type,
        )
        for relationship in relationships
    ] == [("orders", "id", "payments", "order_id", "foreign_key")]


def _column(table_name: str, column_name: str) -> SchemaColumnContext:
    return SchemaColumnContext(
        table_name=table_name,
        column_name=column_name,
        data_type="text",
        description=f"{table_name}.{column_name}",
        business_meaning=f"{table_name}.{column_name}",
    )


def _relationship(
    left_table: str,
    left_column: str,
    right_table: str,
    right_column: str,
    relationship_type: str,
    confidence: float,
    reason: str,
):
    from backend.app.schemas.retrieval import TableRelationshipContext

    return TableRelationshipContext(
        left_table=left_table,
        left_column=left_column,
        right_table=right_table,
        right_column=right_column,
        relationship_type=relationship_type,
        confidence=confidence,
        reason=reason,
    )
