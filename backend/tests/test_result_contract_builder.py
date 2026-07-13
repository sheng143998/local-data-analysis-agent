from backend.app.schemas.sql_execution import SqlExecutionResult
from backend.app.tools.result_contract_builder import build_result_contract


def test_result_contract_marks_plan_measures_and_dimensions() -> None:
    contract = build_result_contract(
        "用户总数", SqlExecutionResult(status="success", columns=["user_total"], rows=[{"user_total": 10}], row_count=1),
        {"measures": [{"name": "user_total"}], "dimensions": []}, [],
    )
    assert contract.columns[0].semantic_role == "metric"
    assert contract.row_count == 1
