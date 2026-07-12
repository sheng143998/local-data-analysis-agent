from datetime import date

from backend.app.tools.query_spec import build_query_spec


def test_query_spec_requires_user_tables_and_rank_output() -> None:
    spec = build_query_spec(
        "购买次数最多的前 10 个用户是谁？",
        metrics=["user_purchase_count"],
        dimensions=["user"],
        time_range="",
    )

    assert spec.required_tables == ["orders", "users"]
    assert spec.required_metric_tokens == ["purchase_count"]
    assert spec.required_dimension_tokens == ["user"]
    assert spec.top_n == 10
    assert spec.requires_order_by is True


def test_query_spec_requires_funnel_tables_and_conversion_output() -> None:
    spec = build_query_spec(
        "最近 30 天访问到下单转化率是多少？",
        metrics=["visit_to_order_conversion_rate"],
        dimensions=[],
        time_range="最近 30 天",
    )

    assert spec.required_tables == ["orders", "traffic_events"]
    assert spec.required_metric_tokens == ["conversion_rate"]
    assert spec.granularity is None


def test_query_spec_uses_half_open_month_and_day_ranges() -> None:
    month = build_query_spec(
        "这个月卖了多少钱？",
        metrics=["sales_amount"],
        dimensions=[],
        time_range="本月",
        today=date(2026, 2, 17),
    )
    day = build_query_spec(
        "2024年2月29日卖了多少钱？",
        metrics=["sales_amount"],
        dimensions=[],
        time_range="2024年2月29日",
        today=date(2026, 2, 17),
    )

    assert month.time_start == "2026-02-01"
    assert month.time_end == "2026-03-01"
    assert "{time_field} >= DATE '2026-02-01'" in month.time_filter
    assert "{time_field} < DATE '2026-03-01'" in month.time_filter
    assert day.time_start == "2024-02-29"
    assert day.time_end == "2024-03-01"


def test_query_spec_uses_full_year_range() -> None:
    spec = build_query_spec(
        "2017年卖了多少钱？",
        metrics=["sales_amount"],
        dimensions=[],
        time_range="2017年",
    )

    assert spec.time_start == "2017-01-01"
    assert spec.time_end == "2018-01-01"
