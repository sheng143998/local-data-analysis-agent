from datetime import datetime, timezone

from backend.app.schemas.sql_execution import SqlExecutionResult
from backend.app.tools.analysis_presenter import present_sales_trend_result
from backend.app.tools.result_contract_builder import build_result_contract


def test_presenter_builds_summary_and_metrics_from_generic_rows() -> None:
    execution = SqlExecutionResult(
        status="success",
        columns=["traffic_source", "conversion_rate", "visitor_count"],
        rows=[
            {"traffic_source": "搜索", "conversion_rate": 12.5, "visitor_count": 1000},
            {"traffic_source": "广告", "conversion_rate": 8.2, "visitor_count": 800},
        ],
        row_count=2,
        latency_ms=18,
    )

    response = present_sales_trend_result(
        question="流量来源带来的订单转化率是多少？",
        sql="SELECT traffic_source, conversion_rate, visitor_count FROM traffic_events",
        execution=execution,
        guard_warnings=[],
        latency_ms=20,
    )

    assert "真实 PostgreSQL 数据" in response.summary
    assert "返回 2 行结果" in response.summary
    assert "traffic source" in response.summary
    assert "conversion rate" in response.summary
    assert response.rows[0]["traffic_source"] == "搜索"
    metric_labels = [metric.label for metric in response.metrics]
    assert "返回行数" in metric_labels
    assert "conversion rate" in metric_labels
    assert response.source.range == "有交易日期维度，返回 2 行"


def test_presenter_keeps_known_business_labels_for_existing_columns() -> None:
    execution = SqlExecutionResult(
        status="success",
        columns=["city_label", "avg_order_value", "order_count"],
        rows=[
            {"city_label": "sao paulo", "avg_order_value": 120.0, "order_count": 3},
        ],
        row_count=1,
        latency_ms=18,
    )

    response = present_sales_trend_result(
        question="每个城市的客单价是多少？",
        sql="SELECT city_label, avg_order_value, order_count FROM orders",
        execution=execution,
        guard_warnings=[],
        latency_ms=20,
    )

    assert "城市客单价" in response.summary
    assert "城市" in response.summary
    assert "客单价" in response.summary
    assert response.metrics[1].label == "客单价"


def test_presenter_reports_successful_empty_result_without_treating_zero_as_empty() -> None:
    empty = SqlExecutionResult(status="success", row_count=0)
    response = present_sales_trend_result(
        question="各流量来源的事件数", sql="SELECT source FROM traffic_events", execution=empty,
        guard_warnings=[], latency_ms=1, result_contract=build_result_contract("各流量来源的事件数", empty, {"time_filter": ""}, []),
    )

    assert response.source.resultState == "empty"
    assert "筛选条件下没有匹配记录" in response.summary


def test_presenter_exposes_deterministic_visualization_from_result_contract() -> None:
    execution = SqlExecutionResult(
        status="success",
        columns=["order_date", "sales_amount"],
        rows=[{"order_date": "2017-01-02", "sales_amount": 20}, {"order_date": "2017-01-01", "sales_amount": 10}],
        row_count=2,
        latency_ms=1,
    )
    contract = build_result_contract(
        "销售趋势", execution, {"dimensions": ["order_date"], "measures": [{"name": "sales_amount"}]}, []
    )

    response = present_sales_trend_result("销售趋势", "SELECT order_date, sales_amount FROM orders", execution, [], 1, result_contract=contract)

    assert response.visualization.kind == "line"
    assert response.visualization.x_field == "order_date"
    assert response.rows[0]["order_date"] == "2017-01-02"


def test_presenter_preserves_monthly_sql_order_and_formats_summary_date() -> None:
    execution = SqlExecutionResult(
        status="success",
        columns=["month", "order_count", "sales_amount"],
        rows=[
            {"month": datetime(2017, 1, 1, tzinfo=timezone.utc), "order_count": 800, "sales_amount": 138488.04},
            {"month": datetime(2017, 12, 1, tzinfo=timezone.utc), "order_count": 5673, "sales_amount": 878401.48},
        ],
        row_count=2,
        latency_ms=1,
    )

    response = present_sales_trend_result(
        "2017 年每个月已支付订单的销售额和订单数分别是多少？",
        "SELECT DATE_TRUNC('MONTH', o.purchase_at) AS month FROM orders o ORDER BY month ASC",
        execution,
        [],
        1,
    )

    assert response.rows[0]["month"] == "2017-01-01T00:00:00+00:00"
    assert "首行月份为 2017-01-01" in response.summary
    assert "2017-12-01" in response.source.range
