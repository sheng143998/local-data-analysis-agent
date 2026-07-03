from backend.app.services.schema_sync_service import (
    DEFAULT_EXCLUDED_TABLES,
    SchemaColumnSnapshot,
    SchemaSyncService,
    infer_schema_business_meaning,
    infer_schema_description,
    _normalize_filter,
)


class FakeCursor:
    def __init__(self) -> None:
        self.statements: list[tuple[str, tuple | None]] = []
        self.rows = [
            ("orders", "id", "text"),
            ("orders", "total_amount", "numeric"),
            ("users", "city", "text"),
        ]

    def execute(self, sql: str, params: tuple | None = None) -> None:
        self.statements.append((sql, params))

    def fetchall(self) -> list[tuple[str, str, str]]:
        return self.rows


def test_normalize_filter_strips_empty_values() -> None:
    assert _normalize_filter([" orders ", "", "users"]) == {"orders", "users"}


def test_load_public_columns_applies_include_and_exclude_filters() -> None:
    cursor = FakeCursor()
    service = SchemaSyncService()

    columns = service._load_public_columns(
        cursor,
        include_tables={"orders", "users"},
        exclude_tables=DEFAULT_EXCLUDED_TABLES,
    )

    assert columns == [
        SchemaColumnSnapshot("orders", "id", "text"),
        SchemaColumnSnapshot("orders", "total_amount", "numeric"),
        SchemaColumnSnapshot("users", "city", "text"),
    ]
    params = cursor.statements[0][1]
    assert params is not None
    assert "orders" in params[1]
    assert "schema_metadata" in params[0]


def test_upsert_schema_metadata_preserves_existing_descriptions() -> None:
    cursor = FakeCursor()
    service = SchemaSyncService()

    synced = service._upsert_schema_metadata(
        cursor,
        [SchemaColumnSnapshot("orders", "created_at", "timestamp with time zone")],
    )

    assert synced == 1
    sql, params = cursor.statements[0]
    assert "ON CONFLICT (table_name, column_name) DO UPDATE" in sql
    assert "schema_metadata.description = ''" in sql
    assert "schema_metadata.description = %s" in sql
    assert params == (
        "orders",
        "created_at",
        "timestamp with time zone",
        "orders.created_at，时间字段，类型为 timestamp with time zone",
        "orders的创建时间，可用于时间趋势、近 N 天筛选和分组。",
        False,
        "orders.created_at",
        False,
        "业务表字段：orders.created_at",
    )


def test_upsert_schema_metadata_can_refresh_generated_descriptions() -> None:
    cursor = FakeCursor()
    service = SchemaSyncService()

    synced = service._upsert_schema_metadata(
        cursor,
        [SchemaColumnSnapshot("orders", "total_amount", "numeric")],
        refresh_generated_descriptions=True,
    )

    assert synced == 1
    _, params = cursor.statements[0]
    assert params == (
        "orders",
        "total_amount",
        "numeric",
        "orders.total_amount，金额字段，类型为 numeric",
        "orders的金额类指标字段，可用于求和、均值、占比和规模分析。",
        True,
        "orders.total_amount",
        True,
        "业务表字段：orders.total_amount",
    )


def test_infer_schema_description_labels_common_field_types() -> None:
    assert "金额字段" in infer_schema_description(
        SchemaColumnSnapshot("orders", "total_amount", "numeric")
    )
    assert "关联标识字段" in infer_schema_description(
        SchemaColumnSnapshot("orders", "user_id", "text")
    )
    assert "时间字段" in infer_schema_description(
        SchemaColumnSnapshot("orders", "paid_at", "timestamp with time zone")
    )


def test_infer_schema_business_meaning_for_common_analysis_fields() -> None:
    assert "金额类指标字段" in infer_schema_business_meaning(
        SchemaColumnSnapshot("orders", "total_amount", "numeric")
    )
    assert "关联user的标识字段" in infer_schema_business_meaning(
        SchemaColumnSnapshot("orders", "user_id", "text")
    )
    assert "地域维度字段" in infer_schema_business_meaning(
        SchemaColumnSnapshot("users", "city", "text")
    )
    assert "分类维度字段" in infer_schema_business_meaning(
        SchemaColumnSnapshot("traffic_events", "source", "text")
    )
