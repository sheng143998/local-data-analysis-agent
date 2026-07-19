from backend.app.schemas.query_spec import QuerySpec
from backend.app.tools.query_planner import build_query_plan
from backend.app.tools.question_intent_parser import ParsedQuestionIntent


def test_query_plan_uses_contract_tables_and_query_spec_shape() -> None:
    intent = ParsedQuestionIntent(
        original_question="销售额最高的前 5 个品类", normalized_question="销售额最高的前 5 个品类",
        query_spec=QuerySpec(metrics=["sales_amount"], dimensions=["category"], top_n=5, requires_order_by=True, required_table_groups=[["orders", "order_items", "products"]]),
        resolved_contracts=[{"contract_key": "sales_amount", "source_tables": ["orders", "order_items"]}],
    )
    plan = build_query_plan(intent)
    assert plan.expected_row_shape == "ranking"
    assert plan.limit == 5
    assert set(plan.entities) == {"orders", "order_items", "products"}
    assert plan.contract_keys == ["sales_amount"]


def test_query_plan_inherits_declarative_shape_from_resolved_contract() -> None:
    intent = ParsedQuestionIntent(
        original_question="销售额最高的前 5 个品类是什么？", normalized_question="销售额最高的前 5 个品类是什么？",
        resolved_contracts=[{
            "contract_key": "category_sales_ranking", "display_name": "品类销售额排行", "source_tables": ["order_items", "products"],
            "source_fields": ["order_items.price", "products.category"], "aggregation": "sum",
            "semantic_config": {"plan": {
                "measures": [{"name": "category_sales_amount", "operation": "sum"}],
                "dimensions": ["category"], "order_by": ["category_sales_amount DESC"], "limit": 5,
                "expected_columns": ["category", "category_sales_amount"], "expected_row_shape": "ranking",
            }},
        }],
    )

    plan = build_query_plan(intent)

    assert plan.entities == ["order_items", "products"]
    assert plan.measures[0].name == "category_sales_amount"
    assert plan.dimensions == ["category"]
    assert plan.order_by == ["category_sales_amount DESC"]
    assert plan.limit == 5
    assert plan.expected_row_shape == "ranking"
    assert plan.contract_constraints[0].source_fields == ["order_items.price", "products.category"]
    assert plan.contract_constraints[0].aggregation == "sum"


def test_query_plan_inherits_payment_status_filter_from_contract() -> None:
    intent = ParsedQuestionIntent(
        original_question="各支付方式已支付金额是多少？",
        normalized_question="各支付方式已支付金额是多少？",
        resolved_contracts=[{
            "contract_key": "payment_method_paid_amount",
            "source_tables": ["payments"],
            "semantic_config": {"plan": {
                "measures": [{"name": "payment_method_paid_amount", "operation": "sum"}],
                "dimensions": ["payment_method"],
                "filters": ["payments.status = 'paid'"],
                "expected_columns": ["payment_method", "payment_method_paid_amount"],
                "expected_row_shape": "grouped",
            }},
        }],
    )

    plan = build_query_plan(intent)

    assert plan.entities == ["payments"]
    assert plan.dimensions == ["payment_type"]
    assert plan.filters == ["payments.status = 'paid'"]
    assert plan.expected_row_shape == "grouped"


def test_query_plan_discards_top_n_language_from_business_filters() -> None:
    intent = ParsedQuestionIntent(original_question="订单商品数最多的前5个品类", normalized_question="订单商品数最多的前5个品类", filters=["前5个"], query_spec=QuerySpec(top_n=5, requires_order_by=True))
    assert build_query_plan(intent).filters == []


def test_query_plan_discards_sort_direction_language_from_business_filters() -> None:
    intent = ParsedQuestionIntent(
        original_question="按订单商品数量降序展示商品品类",
        normalized_question="按订单商品数量降序展示商品品类",
        filters=["按订单商品数量降序"],
    )

    assert build_query_plan(intent).filters == []


def test_query_plan_binds_executable_paid_order_month_contract() -> None:
    intent = ParsedQuestionIntent(
        original_question="2017 年每个月已支付订单的销售额和订单数分别是多少？按月份升序展示。",
        normalized_question="查询2017年每个月已支付订单的销售额和订单数",
        semantic_dimensions=["月份", "每月"],
        filters=["已支付订单"],
        query_spec=QuerySpec(
            metrics=["sales_amount", "order_count"],
            dimensions=["month"],
            time_filter="{time_field} >= DATE '2017-01-01' AND {time_field} < DATE '2018-01-01'",
            required_table_groups=[["orders", "payments"]],
        ),
    )

    plan = build_query_plan(intent)

    assert plan.dimensions == ["month"]
    assert plan.time_filter == "orders.purchase_at >= DATE '2017-01-01' AND orders.purchase_at < DATE '2018-01-01'"
    assert plan.execution_contract.time_field == "orders.purchase_at"
    assert plan.execution_contract.time_group_expression == "DATE_TRUNC('month', orders.purchase_at)"
    assert plan.execution_contract.canonical_filters == ["payments.status = 'paid'"]
    assert plan.filters == ["payments.status = 'paid'"]
    assert plan.execution_contract.aggregation_grain == "order"
    assert len(plan.execution_contract.join_strategy) == 2
    assert plan.execution_contract.output_aliases == {
        "month": "month",
        "sales_amount": "sales_amount",
        "order_count": "order_count",
    }
    assert {"month", "sales_amount", "order_count"} <= set(plan.expected_columns)


def test_query_plan_canonicalizes_short_paid_filter() -> None:
    intent = ParsedQuestionIntent(
        original_question="2017 年已支付订单数是多少？",
        normalized_question="2017 年已支付订单数",
        filters=["已支付"],
        query_spec=QuerySpec(
            metrics=["order_count"],
            time_filter="{time_field} >= DATE '2017-01-01' AND {time_field} < DATE '2018-01-01'",
            required_table_groups=[["orders", "payments"]],
        ),
    )

    plan = build_query_plan(intent)

    assert plan.filters == ["payments.status = 'paid'"]
    assert plan.execution_contract.canonical_filters == ["payments.status = 'paid'"]


def test_query_plan_normalizes_category_synonyms_for_item_sales_ranking() -> None:
    intent = ParsedQuestionIntent(
        original_question="订单商品数量最多的前 10 个商品品类是什么？展示品类、订单商品数量和销售额。",
        normalized_question="订单商品数量最多的前 10 个商品品类",
        semantic_dimensions=["商品品类", "品类", "类目", "分类"],
        query_spec=QuerySpec(top_n=10, requires_order_by=True),
        resolved_contracts=[{
            "contract_key": "category_item_sales_ranking",
            "source_tables": ["orders", "payments", "order_items", "products"],
            "source_fields": ["order_items.id", "order_items.price", "products.category"],
            "aggregation": "sum",
            "semantic_config": {"plan": {
                "measures": [
                    {"name": "order_item_count", "operation": "count"},
                    {"name": "sales_amount", "operation": "sum"},
                ],
                "dimensions": ["category"],
                "filters": ["payments.status = 'paid'"],
                "order_by": ["order_item_count DESC"],
                "expected_columns": ["category", "order_item_count", "sales_amount"],
                "expected_row_shape": "ranking",
            }},
        }],
    )

    plan = build_query_plan(intent)

    assert plan.dimensions == ["category"]
    assert plan.order_by == ["order_item_count DESC"]
    assert plan.limit == 10
    assert plan.execution_contract.canonical_filters == ["payments.status = 'paid'"]
    assert plan.execution_contract.aggregation_grain == "order"
    assert set(plan.expected_columns) == {"category", "order_item_count", "sales_amount"}
