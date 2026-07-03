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


def test_parse_sales_trend_parameters_supports_top_product_sales() -> None:
    params = parse_sales_trend_parameters("销售额最高的前 10 个商品是什么？")

    assert params.metric == "top_product_sales"
    assert params.limit == 10


def test_render_sales_trend_sql_supports_top_category_sales() -> None:
    sql = render_sales_trend_sql(parse_sales_trend_parameters("哪个商品品类销售额最高？"))

    assert "category_label" in sql
    assert "order_items oi" in sql
    assert "products p" in sql
    assert "ORDER BY daily_sales DESC" in sql
    assert "LIMIT 10" in sql


def test_render_sales_trend_sql_supports_category_refund_rate() -> None:
    sql = render_sales_trend_sql(parse_sales_trend_parameters("哪个商品品类退款率最高？"))

    assert "category_label" in sql
    assert "refund_rate" in sql
    assert "ORDER BY refund_rate DESC" in sql


def test_render_sales_trend_sql_supports_payment_success_rate() -> None:
    sql = render_sales_trend_sql(parse_sales_trend_parameters("每个支付方式的成功率是多少？"))

    assert "payment_method_label" in sql
    assert "success_rate" in sql
    assert "payments pay" in sql
