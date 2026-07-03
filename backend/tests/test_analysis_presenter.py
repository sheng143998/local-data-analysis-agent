from backend.app.schemas.sql_execution import SqlExecutionResult
from backend.app.tools.analysis_presenter import present_sales_trend_result


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
    assert response.rows[0]["traffic_source"] == "广告"
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
