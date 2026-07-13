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
