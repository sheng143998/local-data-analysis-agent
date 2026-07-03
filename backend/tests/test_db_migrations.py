from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
MIGRATION_DIR = ROOT / "backend" / "app" / "db" / "migrations"


def test_required_migrations_exist() -> None:
    names = {path.name for path in MIGRATION_DIR.glob("*.sql")}
    assert "001_extensions.sql" in names
    assert "002_business_tables.sql" in names
    assert "003_agent_metadata.sql" in names


def test_business_tables_declared() -> None:
    sql = (MIGRATION_DIR / "002_business_tables.sql").read_text(encoding="utf-8")
    for table in [
        "users",
        "products",
        "orders",
        "order_items",
        "payments",
        "refunds",
        "reviews",
        "traffic_events",
        "coupons",
        "coupon_usages",
        "inventory_snapshots",
        "product_costs",
    ]:
        assert f"CREATE TABLE IF NOT EXISTS {table}" in sql


def test_agent_metadata_tables_declared() -> None:
    sql = (MIGRATION_DIR / "003_agent_metadata.sql").read_text(encoding="utf-8")
    for table in [
        "schema_metadata",
        "metric_definitions",
        "sql_memories",
        "query_runs",
        "tool_calls",
        "embedding_documents",
    ]:
        assert f"CREATE TABLE IF NOT EXISTS {table}" in sql
