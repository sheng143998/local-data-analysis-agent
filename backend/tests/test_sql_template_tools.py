from backend.app.tools.sql_template_tools import (
    MAX_SALES_TREND_DAYS,
    parse_sales_trend_parameters,
    render_sales_trend_sql,
)


def test_parse_sales_trend_parameters_extracts_days() -> None:
    params = parse_sales_trend_parameters("最近 7 天销售额是多少？")

    assert params.days == 7
    assert params.granularity == "day"
    assert params.metric == "sales_amount"


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


def test_parse_sales_trend_parameters_supports_monthly_order_count() -> None:
    params = parse_sales_trend_parameters("最近 90 天每月订单数是多少？")

    assert params.days == 90
    assert params.granularity == "month"
    assert params.metric == "order_count"


def test_render_sales_trend_sql_supports_monthly_bucket_limit() -> None:
    sql = render_sales_trend_sql(parse_sales_trend_parameters("最近 90 天每月订单数是多少？"))

    assert "DATE_TRUNC('month', o.created_at)::date AS order_date" in sql
    assert "GROUP BY DATE_TRUNC('month', o.created_at)::date" in sql
    assert "COUNT(DISTINCT o.id) AS order_count" in sql
    assert "LIMIT 3" in sql
