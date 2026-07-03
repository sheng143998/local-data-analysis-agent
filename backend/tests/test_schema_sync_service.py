from backend.app.services.schema_sync_service import (
    DEFAULT_EXCLUDED_TABLES,
    SchemaColumnSnapshot,
    SchemaSyncService,
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
    assert params == (
        "orders",
        "created_at",
        "timestamp with time zone",
        "orders.created_at",
        "业务表字段：orders.created_at",
    )
