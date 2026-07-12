from sqlglot import exp, parse, parse_one
from sqlglot.errors import ParseError

from backend.app.db.connection import get_connection
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

BLOCKED_FUNCTIONS = {
    "pg_sleep",
    "pg_sleep_for",
    "pg_sleep_until",
    "pg_read_file",
    "pg_read_binary_file",
    "pg_ls_dir",
    "pg_stat_file",
    "dblink_connect",
    "dblink_exec",
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
    cte_names = _cte_names(expression)
    tables = _extract_tables(expression, exclude=cte_names)

    if not isinstance(expression, exp.Select):
        errors.append("只允许 SELECT 查询")

    if _starts_with_write_keyword(sql):
        errors.append("禁止写操作、DDL 或权限变更语句")

    blocked_tables = sorted(set(tables) - set(request.allowed_tables))
    if blocked_tables:
        errors.append(f"访问了非白名单数据表：{', '.join(blocked_tables)}")

    if _has_select_star(expression):
        errors.append("禁止使用 SELECT *，请显式选择字段")

    blocked_functions = _blocked_functions(expression)
    if blocked_functions:
        errors.append(f"禁止调用危险数据库函数：{', '.join(blocked_functions)}")

    if not blocked_tables:
        _validate_field_references(expression, tables, request, errors, warnings)

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
    schema_fields: list[str] | None = None,
) -> SqlGuardResult:
    request = SqlValidationRequest(
        sql=sql,
        allowed_tables=allowed_tables or DEFAULT_ALLOWED_TABLES.copy(),
        max_rows=max_rows,
        schema_fields=schema_fields,
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
    warnings = [*validation.warnings]
    if isinstance(expression, exp.Select):
        limit = expression.args.get("limit")
        limit_value = _limit_value(limit)
        if limit is None:
            expression.set("limit", exp.Limit(expression=exp.Literal.number(max_rows)))
            warnings.append(f"已自动添加 LIMIT {max_rows}")
        elif limit_value is None or limit_value > max_rows:
            expression.set("limit", exp.Limit(expression=exp.Literal.number(max_rows)))
            warnings.append(f"已将 LIMIT 收紧为 {max_rows}")
        final_sql = expression.sql(dialect="postgres")

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


def _extract_tables(expression: exp.Expression, *, exclude: set[str] | None = None) -> list[str]:
    excluded = exclude or set()
    return sorted(
        {
            table.name
            for table in expression.find_all(exp.Table)
            if table.name and table.name not in excluded
        }
    )


def _cte_names(expression: exp.Expression) -> set[str]:
    return {cte.alias for cte in expression.find_all(exp.CTE) if cte.alias}


def _has_select_star(expression: exp.Expression) -> bool:
    return any(isinstance(item, exp.Star) for item in expression.find_all(exp.Star))


def _blocked_functions(expression: exp.Expression) -> list[str]:
    names = {
        function.name.lower()
        for function in expression.find_all(exp.Func)
        if function.name and function.name.lower() in BLOCKED_FUNCTIONS
    }
    return sorted(names)


def _limit_value(limit: exp.Expression | None) -> int | None:
    if not isinstance(limit, exp.Limit) or limit.expression is None:
        return None
    try:
        return int(limit.expression.name)
    except (TypeError, ValueError):
        return None


def _starts_with_write_keyword(sql: str) -> bool:
    first = sql.lstrip().split(maxsplit=1)[0].upper() if sql.strip() else ""
    return first in WRITE_KEYWORDS


def _validate_field_references(
    expression: exp.Expression,
    tables: list[str],
    request: SqlValidationRequest,
    errors: list[str],
    warnings: list[str],
) -> None:
    if not tables:
        return
    schema_fields, schema_warning = _resolve_schema_fields(request, tables)
    if schema_warning:
        warnings.append(schema_warning)
    if schema_fields is None:
        return

    alias_to_table = _table_aliases(expression)
    output_aliases = _output_aliases(expression)
    table_to_columns = _fields_by_table(schema_fields)
    _merge_derived_table_columns(expression, alias_to_table, table_to_columns)
    missing_fields = _missing_field_references(
        expression,
        tables,
        alias_to_table,
        table_to_columns,
        output_aliases,
    )
    if missing_fields:
        errors.append(
            "字段不存在或未在 schema_metadata 中登记："
            + ", ".join(missing_fields)
        )


def _resolve_schema_fields(
    request: SqlValidationRequest,
    tables: list[str],
) -> tuple[set[str] | None, str]:
    if request.schema_fields is not None:
        return {_normalize_field_name(field) for field in request.schema_fields if "." in field}, ""
    try:
        return _load_schema_fields(tables), ""
    except Exception as exc:  # pragma: no cover - defensive fallback for local DB outages
        return None, f"schema_metadata 字段校验不可用：{exc}"


def _load_schema_fields(tables: list[str]) -> set[str]:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT table_name, column_name
            FROM schema_metadata
            WHERE table_name = ANY(%s)
            """,
            (tables,),
        )
        return {
            _normalize_field_name(f"{row[0]}.{row[1]}")
            for row in cursor.fetchall()
        }


def _table_aliases(expression: exp.Expression) -> dict[str, str]:
    aliases: dict[str, str] = {}
    for table in expression.find_all(exp.Table):
        if not table.name:
            continue
        aliases[table.name] = table.name
        if table.alias:
            aliases[table.alias] = table.name
    return aliases


def _merge_derived_table_columns(
    expression: exp.Expression,
    alias_to_table: dict[str, str],
    table_to_columns: dict[str, set[str]],
) -> None:
    for cte in expression.find_all(exp.CTE):
        if not cte.alias:
            continue
        cte_alias = cte.alias
        alias_to_table[cte_alias] = cte_alias
        cte_columns = _select_output_names(cte.this)
        if cte_columns:
            table_to_columns.setdefault(cte_alias, set()).update(cte_columns)

    for subquery in expression.find_all(exp.Subquery):
        if not subquery.alias:
            continue
        derived_alias = subquery.alias
        alias_to_table[derived_alias] = derived_alias
        derived_columns = _select_output_names(subquery.this)
        if derived_columns:
            table_to_columns.setdefault(derived_alias, set()).update(derived_columns)


def _select_output_names(expression: exp.Expression) -> set[str]:
    if not isinstance(expression, exp.Select):
        return set()
    names: set[str] = set()
    for item in expression.expressions:
        if isinstance(item, exp.Alias) and item.alias:
            names.add(item.alias)
            continue
        if isinstance(item, exp.Column) and item.name:
            names.add(item.name)
    return names


def _fields_by_table(schema_fields: set[str]) -> dict[str, set[str]]:
    by_table: dict[str, set[str]] = {}
    for field in schema_fields:
        table_name, column_name = field.split(".", 1)
        by_table.setdefault(table_name, set()).add(column_name)
    return by_table


def _output_aliases(expression: exp.Expression) -> set[str]:
    return {
        alias.alias.lower()
        for alias in expression.find_all(exp.Alias)
        if alias.alias
    }


def _missing_field_references(
    expression: exp.Expression,
    tables: list[str],
    alias_to_table: dict[str, str],
    table_to_columns: dict[str, set[str]],
    output_aliases: set[str],
) -> list[str]:
    missing: set[str] = set()
    for column in expression.find_all(exp.Column):
        if column.name == "*":
            continue
        if not column.table and column.name.lower() in output_aliases:
            continue
        table_name = alias_to_table.get(column.table or "")
        if table_name:
            field_name = _normalize_field_name(f"{table_name}.{column.name}")
            if column.name not in table_to_columns.get(table_name, set()):
                missing.add(field_name)
            continue

        if len(tables) == 1:
            table_name = tables[0]
            field_name = _normalize_field_name(f"{table_name}.{column.name}")
            if column.name not in table_to_columns.get(table_name, set()):
                missing.add(field_name)
            continue

        candidate_tables = [
            table
            for table in tables
            if column.name in table_to_columns.get(table, set())
        ]
        if not candidate_tables:
            missing.add(column.name)
    return sorted(missing)


def _normalize_field_name(field: str) -> str:
    return field.strip().strip('"').lower()
