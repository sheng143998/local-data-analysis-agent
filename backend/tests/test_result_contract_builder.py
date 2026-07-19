from backend.app.schemas.sql_execution import SqlExecutionResult
from backend.app.tools.result_contract_builder import build_result_contract, build_visualization_spec


def test_result_contract_marks_plan_measures_and_dimensions() -> None:
    contract = build_result_contract(
        "用户总数", SqlExecutionResult(status="success", columns=["user_total"], rows=[{"user_total": 10}], row_count=1),
        {"measures": [{"name": "user_total"}], "dimensions": []}, [],
    )
    assert contract.columns[0].semantic_role == "metric"
    assert contract.row_count == 1
    assert contract.result_state == "success"


def test_result_contract_marks_successful_empty_result_without_confusing_zero_value() -> None:
    empty = build_result_contract("流量来源", SqlExecutionResult(status="success", row_count=0), {}, [])
    zero = build_result_contract(
        "流量事件总数", SqlExecutionResult(status="success", columns=["event_count"], rows=[{"event_count": 0}], row_count=1), {}, [],
    )

    assert empty.result_state == "empty"
    assert zero.result_state == "success"


def test_visualization_spec_uses_line_for_time_dimension() -> None:
    contract = build_result_contract(
        "销售趋势",
        SqlExecutionResult(
            status="success",
            columns=["order_date", "sales_amount"],
            rows=[{"order_date": "2017-01-01", "sales_amount": 10}, {"order_date": "2017-01-02", "sales_amount": 20}],
            row_count=2,
        ),
        {"dimensions": ["order_date"], "measures": [{"name": "sales_amount"}]},
        [],
    )

    visualization = build_visualization_spec(contract)

    assert visualization.kind == "line"
    assert visualization.x_field == "order_date"
    assert visualization.y_fields == ["sales_amount"]
    assert visualization.unit == "currency"
    assert visualization.field_labels == {"order_date": "日期", "sales_amount": "销售额"}
    assert visualization.field_units == {"sales_amount": "currency"}


def test_visualization_spec_labels_monthly_sales_and_order_count_for_separate_axes() -> None:
    contract = build_result_contract(
        "2017 年每个月已支付订单的销售额和订单数分别是多少？",
        SqlExecutionResult(
            status="success",
            columns=["month", "order_count", "sales_amount"],
            rows=[
                {"month": "2017-01-01T00:00:00+08:00", "order_count": 800, "sales_amount": 138488.04},
                {"month": "2017-02-01T00:00:00+08:00", "order_count": 1780, "sales_amount": 291908.01},
            ],
            row_count=2,
        ),
        {"dimensions": ["month"], "measures": [{"name": "sales_amount"}, {"name": "order_count"}]},
        [],
    )

    visualization = build_visualization_spec(contract)

    assert visualization.title == "订单数、销售额趋势"
    assert visualization.field_labels == {"month": "月份", "order_count": "订单数", "sales_amount": "销售额"}
    assert visualization.field_units == {"order_count": "number", "sales_amount": "currency"}


def test_visualization_spec_uses_pie_only_for_small_non_rate_composition() -> None:
    contract = build_result_contract(
        "支付状态分布",
        SqlExecutionResult(
            status="success",
            columns=["payment_status", "payment_count"],
            rows=[{"payment_status": "paid", "payment_count": 8}, {"payment_status": "failed", "payment_count": 2}],
            row_count=2,
        ),
        {"dimensions": ["payment_status"], "measures": [{"name": "payment_count"}]},
        [],
    )

    assert build_visualization_spec(contract).kind == "pie"


def test_visualization_spec_keeps_empty_and_single_value_as_table_or_metric() -> None:
    contract = build_result_contract(
        "用户总数", SqlExecutionResult(status="success", columns=["user_total"], rows=[{"user_total": 10}], row_count=1), {}, []
    )

    assert build_visualization_spec(contract).kind == "none"
