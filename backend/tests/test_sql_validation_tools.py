from backend.app.schemas.sql_validation import SqlValidationRequest
from backend.app.tools.sql_validation_tools import guard_sql, validate_sql


def test_validate_accepts_safe_select() -> None:
    result = validate_sql(
        SqlValidationRequest(
            sql="SELECT id, total_amount FROM orders WHERE status = 'delivered' LIMIT 10"
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


def test_guard_injects_limit() -> None:
    result = guard_sql("SELECT id, total_amount FROM orders", max_rows=100)
    assert result.allowed is True
    assert result.final_sql.endswith("LIMIT 100")
    assert "已自动添加 LIMIT 100" in result.warnings
