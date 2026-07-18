from backend.app.tools.sql_inspector import inspect_query_plan


def test_inspector_reports_missing_plan_entity_and_ranking_constraints() -> None:
    issues = inspect_query_plan(
        "SELECT SUM(total_amount) AS sales_amount FROM orders",
        {"entities": ["orders", "products"], "expected_row_shape": "ranking", "limit": 5},
    )
    assert {issue.category for issue in issues} == {"missing_table", "missing_order", "missing_limit"}


def test_inspector_does_not_invent_unknown_plan_constraints() -> None:
    assert inspect_query_plan("SELECT COUNT(*) FROM users", {"expected_row_shape": "unknown"}) == []


def test_inspector_attaches_copyable_rules_to_structural_issues() -> None:
    issues = inspect_query_plan(
        "SELECT SUM(total_amount) AS sales_amount FROM orders",
        {
            "entities": ["orders", "products"],
            "expected_row_shape": "ranking",
            "order_by": ["sales_amount DESC"],
            "limit": 5,
        },
    )

    by_category = {issue.category: issue for issue in issues}
    assert "products" in by_category["missing_table"].repair_rule
    assert "sales_amount DESC" in by_category["missing_order"].repair_rule
    assert "LIMIT 5" in by_category["missing_limit"].repair_rule


def test_inspector_does_not_treat_unrelated_where_as_time_filter() -> None:
    issues = inspect_query_plan(
        "SELECT COUNT(*) FROM orders WHERE status = 'delivered'",
        {
            "entities": ["orders"],
            "time_filter": "{time_field} >= DATE '2017-01-01' AND {time_field} < DATE '2018-01-01'",
        },
    )

    assert [issue.category for issue in issues] == ["time_range"]
    assert ">= 起点" in issues[0].repair_rule


def test_inspector_rejects_contract_field_aggregation_filter_and_shape_mismatch() -> None:
    issues = inspect_query_plan(
        "SELECT p.payment_type, COUNT(p.id) AS payment_method_paid_amount "
        "FROM payments p WHERE p.status = 'pending' GROUP BY p.payment_type "
        "ORDER BY payment_method_paid_amount ASC LIMIT 30",
        {
            "entities": ["payments"],
            "filters": ["payments.status = 'paid'"],
            "order_by": ["payment_method_paid_amount DESC"],
            "limit": 5,
            "expected_columns": ["payment_method", "payment_method_paid_amount"],
            "expected_row_shape": "ranking",
            "contract_constraints": [
                {
                    "contract_key": "payment_method_paid_amount",
                    "display_name": "各支付方式已支付金额",
                    "aggregation": "sum",
                    "source_fields": ["payments.payment_type", "payments.amount", "payments.status"],
                }
            ],
        },
    )

    assert {issue.category for issue in issues} == {
        "contract_source_field", "contract_aggregation", "missing_filter", "missing_output", "invalid_order", "invalid_limit"
    }


def test_inspector_accepts_sql_that_matches_contract_formula_and_result_shape() -> None:
    issues = inspect_query_plan(
        "SELECT p.payment_type AS payment_method, SUM(p.amount) AS payment_method_paid_amount "
        "FROM payments p WHERE p.status = 'paid' GROUP BY p.payment_type "
        "ORDER BY payment_method_paid_amount DESC LIMIT 5",
        {
            "entities": ["payments"],
            "filters": ["payments.status = 'paid'"],
            "order_by": ["payment_method_paid_amount DESC"],
            "limit": 5,
            "expected_columns": ["payment_method", "payment_method_paid_amount"],
            "expected_row_shape": "ranking",
            "contract_constraints": [
                {
                    "contract_key": "payment_method_paid_amount",
                    "display_name": "各支付方式已支付金额",
                    "aggregation": "sum",
                    "source_fields": ["payments.payment_type", "payments.amount", "payments.status"],
                }
            ],
        },
    )

    assert issues == []
