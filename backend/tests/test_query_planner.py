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
            "contract_key": "category_sales_ranking", "source_tables": ["order_items", "products"],
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
