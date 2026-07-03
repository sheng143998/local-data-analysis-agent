from backend.app.schemas.memories import SqlReusePlan
from backend.app.schemas.sql_generation import GeneratedSql
from backend.app.tools.sql_template_tools import (
    parse_sales_trend_parameters,
    render_sales_trend_sql,
)


def generate_or_rewrite_sales_sql(question: str, reuse_plan: SqlReusePlan) -> GeneratedSql:
    """V1 确定性 SQL Generator/Rewriter：支持销售趋势和订单数时间趋势。"""
    parameters = parse_sales_trend_parameters(question)
    sql = render_sales_trend_sql(parameters)

    if reuse_plan.path_type == "rewrite_path":
        return GeneratedSql(
            path="deterministic_rewrite",
            sql=sql,
            parameters=parameters,
            warnings=["已基于历史 SQL Memory 和当前问题参数进行确定性改写"],
        )

    return GeneratedSql(path="template_render", sql=sql, parameters=parameters)
