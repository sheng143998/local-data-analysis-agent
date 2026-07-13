from dataclasses import dataclass

from sqlglot import exp, parse_one
from sqlglot.errors import ParseError


@dataclass(frozen=True)
class InspectionIssue:
    category: str
    message: str


def inspect_query_plan(sql: str, query_plan: dict | None) -> list[InspectionIssue]:
    """在 Guard 前校验 SQL 是否遗漏已确认的计划约束。"""
    if not sql.strip() or not query_plan:
        return []
    try:
        expression = parse_one(sql, dialect="postgres")
    except ParseError:
        return [InspectionIssue("syntax", "SQL 无法解析，不能验证 Query Plan 对齐。")]
    tables = {table.name for table in expression.find_all(exp.Table) if table.name}
    issues: list[InspectionIssue] = []
    missing_entities = sorted(set(query_plan.get("entities", [])) - tables)
    if missing_entities:
        issues.append(InspectionIssue("missing_table", f"SQL 未使用计划实体表：{', '.join(missing_entities)}。"))
    if query_plan.get("expected_row_shape") == "ranking" and not expression.args.get("order"):
        issues.append(InspectionIssue("missing_order", "排行计划缺少 ORDER BY。"))
    if query_plan.get("limit") and not expression.args.get("limit"):
        issues.append(InspectionIssue("missing_limit", "Top N 计划缺少 LIMIT。"))
    time_filter = str(query_plan.get("time_filter") or "")
    if time_filter and "where" not in sql.lower():
        issues.append(InspectionIssue("time_range", "计划包含时间过滤，但 SQL 缺少 WHERE 时间条件。"))
    return issues
