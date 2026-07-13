from backend.app.tools.sql_inspector import inspect_query_plan


def test_inspector_reports_missing_plan_entity_and_ranking_constraints() -> None:
    issues = inspect_query_plan(
        "SELECT SUM(total_amount) AS sales_amount FROM orders",
        {"entities": ["orders", "products"], "expected_row_shape": "ranking", "limit": 5},
    )
    assert {issue.category for issue in issues} == {"missing_table", "missing_order", "missing_limit"}


def test_inspector_does_not_invent_unknown_plan_constraints() -> None:
    assert inspect_query_plan("SELECT COUNT(*) FROM users", {"expected_row_shape": "unknown"}) == []
