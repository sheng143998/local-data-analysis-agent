from backend.app.schemas.sql_validation import SqlValidationRequest
from backend.app.tools import sql_validation_tools
from backend.app.tools.sql_validation_tools import guard_sql, validate_sql


def test_validate_accepts_safe_select() -> None:
    result = validate_sql(
        SqlValidationRequest(
            sql="SELECT id, total_amount FROM orders WHERE status = 'delivered' LIMIT 10",
            schema_fields=["orders.id", "orders.total_amount", "orders.status"],
        )
    )
    assert result.is_valid is True
    assert result.tables == ["orders"]


def test_validate_blocks_select_star() -> None:
    result = validate_sql(SqlValidationRequest(sql="SELECT * FROM orders LIMIT 10"))
    assert result.is_valid is False
    assert "禁止使用 SELECT *" in result.errors[0]


def test_guard_blocks_write_sql() -> None:
    result = guard_sql("DELETE FROM orders WHERE id = '1'")
    assert result.allowed is False
    assert "只允许 SELECT 查询" in result.errors


def test_guard_blocks_multi_statement() -> None:
    result = guard_sql("SELECT id FROM orders; SELECT id FROM users")
    assert result.allowed is False
    assert "只允许单条 SQL 语句" in result.errors


def test_guard_blocks_non_whitelist_table() -> None:
    result = guard_sql("SELECT id FROM admin_users LIMIT 10")
    assert result.allowed is False
    assert result.errors == ["访问了非白名单数据表：admin_users"]


def test_validate_blocks_missing_schema_field() -> None:
    result = validate_sql(
        SqlValidationRequest(
            sql="SELECT missing_column FROM orders LIMIT 10",
            schema_fields=["orders.id", "orders.total_amount"],
        )
    )

    assert result.is_valid is False
    assert result.errors == ["字段不存在或未在 schema_metadata 中登记：orders.missing_column"]


def test_validate_accepts_join_alias_fields_and_output_alias() -> None:
    result = validate_sql(
        SqlValidationRequest(
            sql=(
                "SELECT o.id, SUM(p.amount) AS paid_amount "
                "FROM orders o JOIN payments p ON p.order_id = o.id "
                "GROUP BY o.id ORDER BY paid_amount DESC LIMIT 10"
            ),
            schema_fields=[
                "orders.id",
                "payments.amount",
                "payments.order_id",
            ],
        )
    )

    assert result.is_valid is True
    assert result.errors == []


def test_validate_accepts_derived_table_output_fields() -> None:
    result = validate_sql(
        SqlValidationRequest(
            sql=(
                "SELECT user_summary.user_id, user_summary.sales_amount "
                "FROM ("
                "  SELECT o.user_id AS user_id, SUM(o.total_amount) AS sales_amount "
                "  FROM orders o GROUP BY o.user_id"
                ") AS user_summary LIMIT 10"
            ),
            schema_fields=[
                "orders.user_id",
                "orders.total_amount",
            ],
        )
    )

    assert result.is_valid is True
    assert result.errors == []


def test_validate_warns_when_schema_metadata_unavailable(monkeypatch) -> None:
    def fail_load_schema_fields(tables):
        raise RuntimeError("database offline")

    monkeypatch.setattr(sql_validation_tools, "_load_schema_fields", fail_load_schema_fields)

    result = validate_sql(SqlValidationRequest(sql="SELECT id FROM orders LIMIT 10"))

    assert result.is_valid is True
    assert result.warnings == ["schema_metadata 字段校验不可用：database offline"]


def test_guard_injects_limit() -> None:
    result = guard_sql(
        "SELECT id, total_amount FROM orders",
        max_rows=100,
        schema_fields=["orders.id", "orders.total_amount"],
    )
    assert result.allowed is True
    assert result.final_sql.endswith("LIMIT 100")
    assert "已自动添加 LIMIT 100" in result.warnings
