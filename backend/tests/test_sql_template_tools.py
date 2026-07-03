from backend.app.tools.sql_template_tools import (
    MAX_SALES_TREND_DAYS,
    parse_sales_trend_parameters,
    render_sales_trend_sql,
)


def test_parse_sales_trend_parameters_extracts_days() -> None:
    params = parse_sales_trend_parameters("最近 7 天销售额是多少？")

    assert params.days == 7
    assert params.granularity == "day"


def test_parse_sales_trend_parameters_supports_common_period_words() -> None:
    assert parse_sales_trend_parameters("近一周销售趋势").days == 7
    assert parse_sales_trend_parameters("最近一个月销售趋势").days == 30
    assert parse_sales_trend_parameters("最近三个月销售趋势").days == 90


def test_parse_sales_trend_parameters_bounds_large_days() -> None:
    params = parse_sales_trend_parameters("最近 999 天销售额是多少？")

    assert params.days == MAX_SALES_TREND_DAYS


def test_render_sales_trend_sql_uses_limit_days() -> None:
    sql = render_sales_trend_sql(parse_sales_trend_parameters("最近 7 天销售额是多少？"))

    assert "LIMIT 7" in sql
    assert "orders o" in sql
    assert "payments p" in sql
