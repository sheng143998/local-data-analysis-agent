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


def test_inspector_accepts_paid_category_item_sales_ranking() -> None:
    issues = inspect_query_plan(
        "SELECT COALESCE(pr.category, 'uncategorized') AS category, "
        "COUNT(oi.id) AS order_item_count, SUM(oi.price) AS sales_amount "
        "FROM orders o JOIN order_items oi ON oi.order_id = o.id "
        "JOIN products pr ON pr.id = oi.product_id "
        "WHERE EXISTS (SELECT 1 FROM payments pay "
        "WHERE pay.order_id = o.id AND pay.status = 'paid') "
        "GROUP BY COALESCE(pr.category, 'uncategorized') "
        "ORDER BY order_item_count DESC LIMIT 10",
        {
            "entities": ["orders", "payments", "order_items", "products"],
            "filters": ["payments.status = 'paid'"],
            "order_by": ["order_item_count DESC"],
            "limit": 10,
            "expected_columns": ["category", "order_item_count", "sales_amount"],
            "expected_row_shape": "ranking",
            "contract_constraints": [{
                "contract_key": "category_item_sales_ranking",
                "display_name": "品类订单商品数与销售额排行",
                "aggregation": "sum",
                "source_fields": [
                    "orders.id", "payments.order_id", "payments.status",
                    "order_items.id", "order_items.order_id", "order_items.price",
                    "order_items.product_id", "products.id", "products.category",
                ],
            }],
        },
    )

    assert issues == []


def test_inspector_accepts_deduplicated_paid_subquery_for_contract_fields() -> None:
    issues = inspect_query_plan(
        "SELECT p.category AS category, COUNT(oi.id) AS order_item_count, SUM(oi.price) AS sales_amount "
        "FROM order_items oi JOIN orders o ON o.id = oi.order_id "
        "JOIN products p ON p.id = oi.product_id "
        "JOIN (SELECT DISTINCT order_id FROM payments WHERE status = 'paid') paid ON paid.order_id = o.id "
        "GROUP BY p.category ORDER BY order_item_count DESC LIMIT 10",
        {
            "entities": ["orders", "payments", "order_items", "products"],
            "filters": ["payments.status = 'paid'"],
            "order_by": ["order_item_count DESC"],
            "limit": 10,
            "expected_columns": ["category", "order_item_count", "sales_amount"],
            "expected_row_shape": "ranking",
            "contract_constraints": [{
                "contract_key": "category_item_sales_ranking",
                "display_name": "品类订单商品数与销售额排行",
                "aggregation": "sum",
                "source_fields": [
                    "payments.order_id", "payments.status", "order_items.id", "order_items.price",
                    "order_items.order_id", "order_items.product_id", "products.id", "products.category",
                ],
            }],
        },
    )

    assert issues == []
