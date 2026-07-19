from dataclasses import dataclass
import re

from sqlglot import exp, parse_one
from sqlglot.errors import ParseError


@dataclass(frozen=True)
class InspectionIssue:
    category: str
    message: str
    # 业务规则：把结构化检查结果转成模型可以直接执行的修复指令，避免只传递模糊错误。
    repair_rule: str = ""


def inspect_query_plan(sql: str, query_plan: dict | None) -> list[InspectionIssue]:
    """在 Guard 前以 AST 校验已确认的计划与业务合同，禁止错误口径进入数据库。"""
    if not sql.strip() or not query_plan:
        return []
    try:
        expression = parse_one(sql, dialect="postgres")
    except ParseError:
        return [
            InspectionIssue(
                "syntax",
                "SQL 无法解析，不能验证 Query Plan 对齐。",
                "只输出一条可解析的 PostgreSQL SELECT；检查括号、逗号、引号和表别名，不输出 Markdown、解释文字或多条语句。",
            )
        ]

    tables = {table.name for table in expression.find_all(exp.Table) if table.name}
    aliases = _table_aliases(expression)
    fields = _referenced_fields(expression, aliases, tables)
    issues: list[InspectionIssue] = []
    issues.extend(_inspect_entities(query_plan, tables))
    issues.extend(_inspect_contract_constraints(query_plan, expression, fields))
    issues.extend(_inspect_filters(query_plan, expression, aliases, sql))
    issues.extend(_inspect_output_shape(query_plan, expression))
    issues.extend(_inspect_time_filter(query_plan, expression, sql))
    return issues


def _inspect_entities(query_plan: dict, tables: set[str]) -> list[InspectionIssue]:
    missing_entities = sorted(set(query_plan.get("entities", [])) - tables)
    if not missing_entities:
        return []
    names = ", ".join(missing_entities)
    return [
        InspectionIssue(
            "missing_table",
            f"SQL 未使用计划实体表：{names}。",
            f"必须在 FROM 或 JOIN 中使用计划实体表 {names}；只能从 allowed_tables/schema_fields 选择真实表和连接字段，不要因为召回上下文中存在其他表而额外 JOIN。",
        )
    ]


def _inspect_contract_constraints(
    query_plan: dict,
    expression: exp.Expression,
    fields: set[str],
) -> list[InspectionIssue]:
    issues: list[InspectionIssue] = []
    for raw in query_plan.get("contract_constraints", []):
        if not isinstance(raw, dict):
            continue
        key = str(raw.get("contract_key") or "业务合同")
        display_name = str(raw.get("display_name") or key)
        required_fields = [str(field) for field in raw.get("source_fields", []) if field]
        missing_fields = [field for field in required_fields if field.lower() not in fields]
        if missing_fields:
            names = ", ".join(missing_fields)
            issues.append(
                InspectionIssue(
                    "contract_source_field",
                    f"{display_name} 未使用合同要求的来源字段：{names}。",
                    f"这是已确认的 {display_name} 口径，SQL 必须实际引用字段 {names}；不得以其他实体、字段或 COUNT(*) 替代该业务口径。",
                )
            )
        aggregation = str(raw.get("aggregation") or "").strip().lower()
        if aggregation and not _has_aggregation(expression, aggregation):
            issues.append(
                InspectionIssue(
                    "contract_aggregation",
                    f"{display_name} 未满足合同聚合方式：{aggregation}。",
                    f"这是已确认的 {display_name} 口径，必须使用 {aggregation} 聚合；不能改写成其他聚合、行级计算或列表结果。",
                )
            )
    return issues


def _inspect_filters(
    query_plan: dict,
    expression: exp.Expression,
    aliases: dict[str, str],
    sql: str,
) -> list[InspectionIssue]:
    issues: list[InspectionIssue] = []
    for required_filter in [str(item) for item in query_plan.get("filters", []) if item]:
        if _has_required_filter(expression, aliases, sql, required_filter):
            continue
        issues.append(
            InspectionIssue(
                "missing_filter",
                f"SQL 未满足计划业务过滤：{required_filter}。",
                f"必须保留已确认的业务过滤 {required_filter}；使用真实表别名表达同一字段和值，不得删除、反转或替换过滤口径。",
            )
        )
    return issues


def _inspect_output_shape(query_plan: dict, expression: exp.Expression) -> list[InspectionIssue]:
    issues: list[InspectionIssue] = []
    expected_columns = {str(item).lower() for item in query_plan.get("expected_columns", []) if item}
    output_names = _output_names(expression)
    missing_outputs = sorted(expected_columns - output_names)
    if missing_outputs:
        names = ", ".join(missing_outputs)
        issues.append(
            InspectionIssue(
                "missing_output",
                f"SQL 未输出计划要求的列或别名：{names}。",
                f"必须在最终 SELECT 中输出并使用稳定别名 {names}；不能只在 CTE、ORDER BY 或内部表达式中出现。",
            )
        )

    expected_order = [str(item) for item in query_plan.get("order_by", []) if item]
    if query_plan.get("expected_row_shape") == "ranking" and not expression.args.get("order"):
        hint = ", ".join(expected_order)
        issues.append(
            InspectionIssue(
                "missing_order",
                "排行计划缺少 ORDER BY。",
                f"这是排行结果，必须在 SELECT 中保留排行维度和度量，并加入 ORDER BY {hint or '计划度量'}；不能仅按主键或任意字段排序。",
            )
        )
    elif expected_order and not _matches_order(expression, expected_order):
        issues.append(
            InspectionIssue(
                "invalid_order",
                f"SQL 排序不符合计划：需要 {', '.join(expected_order)}。",
                f"必须按计划精确排序 {', '.join(expected_order)}；“最高、最多、前 N”应使用 DESC，不能以 ASC 或其他字段替代。",
            )
        )

    required_limit = query_plan.get("limit")
    actual_limit = _limit_value(expression)
    if isinstance(required_limit, int) and required_limit > 0:
        if actual_limit is None:
            issues.append(
                InspectionIssue(
                    "missing_limit",
                    "Top N 计划缺少 LIMIT。",
                    f"必须加入 LIMIT {required_limit} 以满足 Top N 计划；只使用计划给定的数量，且不得超过 SQL Guard 的行数上限。",
                )
            )
        elif actual_limit != required_limit:
            issues.append(
                InspectionIssue(
                    "invalid_limit",
                    f"SQL LIMIT 为 {actual_limit}，与计划要求的 {required_limit} 不一致。",
                    f"必须使用 LIMIT {required_limit}；不能以更大、较小或通用默认 LIMIT 改变 Top N 结果。",
                )
            )
    return issues


def _inspect_time_filter(query_plan: dict, expression: exp.Expression, sql: str) -> list[InspectionIssue]:
    time_filter = str(query_plan.get("time_filter") or "")
    if not time_filter or _has_time_predicate(sql, time_filter, expression):
        return []
    return [
        InspectionIssue(
            "time_range",
            "计划包含时间过滤，但 SQL 缺少 WHERE 时间条件。",
            f"必须在 WHERE 中加入完整半开时间区间：{time_filter}；将 {{time_field}} 替换为允许的真实时间字段，使用 >= 起点和 < 终点，不得只写单侧条件。",
        )
    ]


def _table_aliases(expression: exp.Expression) -> dict[str, str]:
    aliases: dict[str, str] = {}
    for table in expression.find_all(exp.Table):
        if not table.name:
            continue
        aliases[table.name.lower()] = table.name.lower()
        if table.alias:
            aliases[table.alias.lower()] = table.name.lower()
    return aliases


def _referenced_fields(
    expression: exp.Expression,
    aliases: dict[str, str],
    tables: set[str],
) -> set[str]:
    fields: set[str] = set()
    for column in expression.find_all(exp.Column):
        if not column.name or column.name == "*":
            continue
        if column.table:
            table = aliases.get(column.table.lower(), column.table.lower())
            fields.add(f"{table}.{column.name.lower()}")
            continue
        # 无表前缀只在其所属 SELECT 的局部单表作用域内才可无歧义映射。
        # 例如支付去重子查询 `SELECT DISTINCT order_id FROM payments WHERE status = 'paid'`。
        local_tables = _local_select_tables(column)
        if len(local_tables) == 1:
            fields.add(f"{next(iter(local_tables))}.{column.name.lower()}")
    return fields


def _local_select_tables(column: exp.Column) -> set[str]:
    current = column.parent
    while current is not None and not isinstance(current, exp.Select):
        current = current.parent
    if not isinstance(current, exp.Select):
        return set()

    tables: set[str] = set()
    from_clause = current.args.get("from_")
    if isinstance(from_clause, exp.From) and isinstance(from_clause.this, exp.Table) and from_clause.this.name:
        tables.add(from_clause.this.name.lower())
    for join in current.args.get("joins") or []:
        if isinstance(join, exp.Join) and isinstance(join.this, exp.Table) and join.this.name:
            tables.add(join.this.name.lower())
    return tables


def _has_aggregation(expression: exp.Expression, aggregation: str) -> bool:
    aggregations = {
        "count": exp.Count,
        "count_distinct": exp.Count,
        "sum": exp.Sum,
        "avg": exp.Avg,
        "min_max": (exp.Min, exp.Max),
    }
    expected = aggregations.get(aggregation)
    if expected is None:
        return True
    if aggregation == "min_max":
        return any(expression.find_all(exp.Min)) and any(expression.find_all(exp.Max))
    matches = list(expression.find_all(expected))
    if aggregation != "count_distinct":
        return bool(matches)
    return any(isinstance(item.this, exp.Distinct) for item in matches)


def _has_required_filter(
    expression: exp.Expression,
    aliases: dict[str, str],
    sql: str,
    required_filter: str,
) -> bool:
    normalized = re.sub(r"\s+", "", required_filter.lower()).replace("''", "'")
    match = re.fullmatch(r"([a-z_]+)\.([a-z_]+)=['\"]?([^'\"]+)['\"]?", normalized)
    if not match:
        return normalized in re.sub(r"\s+", "", sql.lower())
    table_name, column_name, value = match.groups()
    for equality in expression.find_all(exp.EQ):
        left, right = equality.left, equality.right
        for column, literal in ((left, right), (right, left)):
            if not isinstance(column, exp.Column) or not isinstance(literal, exp.Literal):
                continue
            actual_table = aliases.get((column.table or "").lower(), (column.table or "").lower())
            if not actual_table:
                local_tables = _local_select_tables(column)
                actual_table = next(iter(local_tables)) if len(local_tables) == 1 else ""
            if actual_table == table_name and column.name.lower() == column_name and str(literal.this).lower() == value.lower():
                return True
    return False


def _output_names(expression: exp.Expression) -> set[str]:
    if not isinstance(expression, exp.Select):
        return set()
    names: set[str] = set()
    for item in expression.expressions:
        if isinstance(item, exp.Alias) and item.alias:
            names.add(item.alias.lower())
        elif isinstance(item, exp.Column) and item.name:
            names.add(item.name.lower())
    return names


def _matches_order(expression: exp.Expression, expected_order: list[str]) -> bool:
    order = expression.args.get("order")
    if not isinstance(order, exp.Order):
        return False
    actual: list[tuple[str, str]] = []
    for item in order.expressions:
        value = item.this
        if isinstance(value, exp.Column):
            name = value.name.lower()
        else:
            name = value.sql(dialect="postgres").lower()
        actual.append((name, "DESC" if item.args.get("desc") else "ASC"))
    required: list[tuple[str, str]] = []
    for item in expected_order:
        parts = item.strip().rsplit(" ", 1)
        name = parts[0].strip().lower()
        direction = parts[1].upper() if len(parts) == 2 and parts[1].upper() in {"ASC", "DESC"} else "ASC"
        required.append((name, direction))
    return actual[: len(required)] == required


def _limit_value(expression: exp.Expression) -> int | None:
    limit = expression.args.get("limit")
    if not isinstance(limit, exp.Limit) or limit.expression is None:
        return None
    try:
        return int(limit.expression.name)
    except (TypeError, ValueError):
        return None


def _has_time_predicate(sql: str, time_filter: str, expression: exp.Expression) -> bool:
    """业务规则：有明确边界时校验两个边界，避免任意 WHERE 被误当成时间过滤。"""
    if expression.args.get("where") is None:
        return False
    bounds = re.findall(r"\d{4}-\d{2}-\d{2}(?:[T ][0-9:.+-]+)?", time_filter)
    if len(bounds) < 2:
        return True
    lowered = sql.lower()
    return all(bound.lower() in lowered for bound in bounds)
