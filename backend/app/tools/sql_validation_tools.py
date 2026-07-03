from sqlglot import exp, parse, parse_one
from sqlglot.errors import ParseError

from backend.app.schemas.sql_validation import (
    DEFAULT_ALLOWED_TABLES,
    SqlGuardResult,
    SqlValidationRequest,
    SqlValidationResult,
)


WRITE_KEYWORDS = {
    "INSERT",
    "UPDATE",
    "DELETE",
    "DROP",
    "ALTER",
    "TRUNCATE",
    "CREATE",
    "REPLACE",
    "MERGE",
    "GRANT",
    "REVOKE",
}


def validate_sql(request: SqlValidationRequest) -> SqlValidationResult:
    errors: list[str] = []
    warnings: list[str] = []
    sql = _strip_sql(request.sql)

    if not sql:
        return SqlValidationResult(is_valid=False, errors=["SQL 不能为空"])

    expressions = _parse_all(sql, errors)
    if errors:
        return SqlValidationResult(is_valid=False, errors=errors)

    if len(expressions) != 1:
        errors.append("只允许单条 SQL 语句")
        return SqlValidationResult(is_valid=False, errors=errors)

    expression = expressions[0]
    tables = _extract_tables(expression)

    if not isinstance(expression, exp.Select):
        errors.append("只允许 SELECT 查询")

    if _starts_with_write_keyword(sql):
        errors.append("禁止写操作、DDL 或权限变更语句")

    blocked_tables = sorted(set(tables) - set(request.allowed_tables))
    if blocked_tables:
        errors.append(f"访问了非白名单数据表：{', '.join(blocked_tables)}")

    if _has_select_star(expression):
        errors.append("禁止使用 SELECT *，请显式选择字段")

    if isinstance(expression, exp.Select) and expression.args.get("limit") is None:
        warnings.append("查询缺少 LIMIT，Guard 会自动补充")

    return SqlValidationResult(
        is_valid=not errors,
        errors=errors,
        warnings=warnings,
        tables=tables,
        normalized_sql=expression.sql(dialect="postgres"),
    )


def guard_sql(
    sql: str,
    allowed_tables: list[str] | None = None,
    max_rows: int = 1000,
) -> SqlGuardResult:
    request = SqlValidationRequest(
        sql=sql,
        allowed_tables=allowed_tables or DEFAULT_ALLOWED_TABLES.copy(),
        max_rows=max_rows,
    )
    validation = validate_sql(request)
    if not validation.is_valid:
        return SqlGuardResult(
            allowed=False,
            errors=validation.errors,
            warnings=validation.warnings,
        )

    final_sql = validation.normalized_sql.rstrip(";")
    expression = parse_one(final_sql, dialect="postgres")
    if isinstance(expression, exp.Select) and expression.args.get("limit") is None:
        final_sql = f"{final_sql} LIMIT {max_rows}"
        warnings = [*validation.warnings, f"已自动添加 LIMIT {max_rows}"]
    else:
        warnings = validation.warnings

    return SqlGuardResult(
        allowed=True,
        final_sql=final_sql,
        errors=[],
        warnings=warnings,
    )


def _strip_sql(sql: str) -> str:
    return sql.strip().strip(";").strip()


def _parse_all(sql: str, errors: list[str]) -> list[exp.Expression]:
    try:
        return [item for item in parse(sql, read="postgres") if item is not None]
    except ParseError as exc:
        errors.append(f"SQL 语法解析失败：{exc}")
        return []


def _extract_tables(expression: exp.Expression) -> list[str]:
    return sorted({table.name for table in expression.find_all(exp.Table) if table.name})


def _has_select_star(expression: exp.Expression) -> bool:
    return any(isinstance(item, exp.Star) for item in expression.find_all(exp.Star))


def _starts_with_write_keyword(sql: str) -> bool:
    first = sql.lstrip().split(maxsplit=1)[0].upper() if sql.strip() else ""
    return first in WRITE_KEYWORDS
