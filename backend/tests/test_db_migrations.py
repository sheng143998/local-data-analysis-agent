from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
MIGRATION_DIR = ROOT / "backend" / "app" / "db" / "migrations"


def test_required_migrations_exist() -> None:
    names = {path.name for path in MIGRATION_DIR.glob("*.sql")}
    assert "001_extensions.sql" in names
    assert "002_business_tables.sql" in names
    assert "003_agent_metadata.sql" in names
    assert "007_conversation_states.sql" in names
    assert "008_semantic_contracts.sql" in names


def test_conversation_state_persistence_declared() -> None:
    sql = (MIGRATION_DIR / "007_conversation_states.sql").read_text(encoding="utf-8")
    assert "CREATE TABLE IF NOT EXISTS conversation_states" in sql
    assert "owner_id UUID REFERENCES app_users" in sql
    assert "state JSONB NOT NULL" in sql


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


def test_semantic_contract_versioning_declared() -> None:
    sql = (MIGRATION_DIR / "008_semantic_contracts.sql").read_text(encoding="utf-8")
    assert "CREATE TABLE IF NOT EXISTS semantic_contracts" in sql
    assert "UNIQUE (contract_key, version)" in sql
    assert "idx_semantic_contracts_key_status_version" in sql


def test_complex_semantic_contract_seed_declares_business_definitions_only() -> None:
    sql = (MIGRATION_DIR / "012_complex_semantic_contracts.sql").read_text(encoding="utf-8")
    assert "category_sales_ranking" in sql
    assert "late_delivery_order_total" in sql
    assert "SELECT " not in sql.upper()
