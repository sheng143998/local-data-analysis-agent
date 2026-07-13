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
    """在 Guard 前校验 SQL 是否遗漏已确认的计划约束，并产出可复制修复规则。"""
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
    issues: list[InspectionIssue] = []
    missing_entities = sorted(set(query_plan.get("entities", [])) - tables)
    if missing_entities:
        names = ", ".join(missing_entities)
        issues.append(
            InspectionIssue(
                "missing_table",
                f"SQL 未使用计划实体表：{names}。",
                f"必须在 FROM 或 JOIN 中使用计划实体表 {names}；只能从 allowed_tables/schema_fields 选择真实表和连接字段，不要因为召回上下文中存在其他表而额外 JOIN。",
            )
        )
    if query_plan.get("expected_row_shape") == "ranking" and not expression.args.get("order"):
        order_by = ", ".join(str(item) for item in query_plan.get("order_by", []) if item)
        order_hint = f"，优先使用计划排序 {order_by}" if order_by else "，按计划度量从高到低或从低到高排序"
        issues.append(
            InspectionIssue(
                "missing_order",
                "排行计划缺少 ORDER BY。",
                f"这是排行结果，必须在 SELECT 中保留排行维度和度量，并加入 ORDER BY{order_hint}；不能仅按主键或任意字段排序。",
            )
        )
    if query_plan.get("limit") and not expression.args.get("limit"):
        limit = int(query_plan["limit"])
        issues.append(
            InspectionIssue(
                "missing_limit",
                "Top N 计划缺少 LIMIT。",
                f"必须加入 LIMIT {limit} 以满足 Top N 计划；只使用计划给定的数量，且不得超过 SQL Guard 的行数上限。",
            )
        )
    time_filter = str(query_plan.get("time_filter") or "")
    if time_filter and not _has_time_predicate(sql, time_filter, expression):
        issues.append(
            InspectionIssue(
                "time_range",
                "计划包含时间过滤，但 SQL 缺少 WHERE 时间条件。",
                f"必须在 WHERE 中加入完整半开时间区间：{time_filter}；将 {{time_field}} 替换为允许的真实时间字段，使用 >= 起点和 < 终点，不得只写单侧条件。",
            )
        )
    return issues


def _has_time_predicate(sql: str, time_filter: str, expression: exp.Expression) -> bool:
    """业务规则：有明确边界时校验两个边界，避免任意 WHERE 被误当成时间过滤。"""
    where = expression.args.get("where")
    if where is None:
        return False
    bounds = re.findall(r"\d{4}-\d{2}-\d{2}(?:[T ][0-9:.+-]+)?", time_filter)
    if len(bounds) < 2:
        return True
    lowered = sql.lower()
    return all(bound.lower() in lowered for bound in bounds)
