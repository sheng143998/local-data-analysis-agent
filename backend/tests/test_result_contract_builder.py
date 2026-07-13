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
