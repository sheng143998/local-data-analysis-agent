from backend.app.core.model_adapter import ModelResponse, ModelUsage
from backend.app.schemas.memories import SqlReusePlan
from backend.app.schemas.retrieval import (
    MetricContext,
    RetrievalContext,
    SchemaColumnContext,
    TableRelationshipContext,
)
from backend.app.tools.model_sql_generator import (
    build_sql_generation_payload,
    build_sql_generation_messages,
    generate_sql_with_model,
    parse_model_sql_response,
)
from backend.app.tools.sql_validation_tools import guard_sql


class FakeAdapter:
    def __init__(self, response: ModelResponse):
        self.response = response
        self.requests = []

    def chat(self, request):
        self.requests.append(request)
        return self.response


def test_build_sql_generation_messages_uses_retrieved_context_only() -> None:
    messages = build_sql_generation_messages(
        "最近 7 天销售额是多少？",
        _context(),
        _plan(),
    )

    assert messages[0].role == "system"
    assert "只生成 PostgreSQL SELECT 查询" in messages[0].content
    assert messages[1].role == "user"
    assert "orders.total_amount" in messages[1].content
    assert "table_relationships" in messages[1].content
    assert "orders.id" in messages[1].content
    assert "payments.order_id" in messages[1].content
    assert "metric_definitions" not in messages[1].content


def test_build_sql_generation_payload_contains_context_contract() -> None:
    payload = build_sql_generation_payload(
        "按支付方式统计销售额",
        _context(relationship_type="foreign_key"),
        _plan(
            path_type="rewrite_path",
            reuse_type="dimension_extend",
            selected_sql="SELECT o.id FROM orders o LIMIT 10",
        ),
    )

    assert payload["allowed_tables"] == ["orders", "payments"]
    assert payload["allowed_fields"] == [
        "orders.id",
        "orders.created_at",
        "orders.total_amount",
        "payments.order_id",
    ]
    assert payload["metrics"][0]["metric_name"] == "sales_amount"
    assert payload["schema_fields"][2] == {
        "table": "orders",
        "column": "total_amount",
        "type": "numeric",
        "meaning": "订单金额",
    }
    assert payload["table_relationships"] == [
        {
            "left": "orders.id",
            "right": "payments.order_id",
            "type": "foreign_key",
            "confidence": 0.92,
            "reason": "payments.order_id 命名上指向 orders.id",
        }
    ]
    assert payload["reuse_plan"] == {
        "path_type": "rewrite_path",
        "reuse_type": "dimension_extend",
        "selected_sql": "SELECT o.id FROM orders o LIMIT 10",
    }
    assert any("Validator" in requirement for requirement in payload["requirements"])


def test_build_sql_generation_payload_includes_intent_and_metric_semantics() -> None:
    payload = build_sql_generation_payload(
        "2017年卖了多少钱，平均卖了多少钱",
        _context(relationship_type="foreign_key"),
        _plan(),
        question_intent={
            "original_question": "2017年卖了多少钱，平均卖了多少钱",
            "normalized_question": "查询2017年总销售额和客单价",
            "metrics": ["sales_amount", "avg_order_value"],
            "dimensions": [],
            "semantic_metrics": ["累计交易金额", "平均订单金额"],
            "semantic_dimensions": [],
            "time_range": "2017年",
            "confidence": 0.9,
            "needs_clarification": False,
            "source": "llm",
            "query_spec": {
                "metrics": ["sales_amount", "avg_order_value"],
                "required_table_groups": [["orders", "payments"]],
                "required_metric_tokens": ["total_amount", "avg_order_value"],
            },
            "clarification": "internal details should not be forwarded",
        },
    )

    assert payload["question_intent"]["metrics"] == ["sales_amount", "avg_order_value"]
    assert payload["question_intent"]["semantic_metrics"] == ["累计交易金额", "平均订单金额"]
    assert payload["question_intent"]["time_range"] == "2017年"
    assert payload["question_intent"]["query_spec"]["required_metric_tokens"] == ["total_amount", "avg_order_value"]
    assert "clarification" not in payload["question_intent"]
    assert payload["metric_semantics"]["sales_amount"]["grain"] == "order"
    assert "COUNT(DISTINCT orders.id)" in payload["metric_semantics"]["avg_order_value"]["preferred_formula"]
    assert any("重复累计" in requirement for requirement in payload["requirements"])


def test_build_sql_generation_payload_preserves_current_entity_total_semantics() -> None:
    payload = build_sql_generation_payload(
        "当前用户总数是多少？",
        _context(relationship_type="foreign_key"),
        _plan(),
        question_intent={
            "original_question": "当前用户总数是多少？",
            "normalized_question": "查询当前用户总数",
            "metrics": [],
            "dimensions": [],
            "semantic_metrics": ["当前用户总数"],
            "semantic_dimensions": [],
            "time_range": "",
            "confidence": 0.85,
            "needs_clarification": False,
            "source": "llm",
            "query_spec": {},
        },
    )

    assert payload["question_intent"]["semantic_metrics"] == ["当前用户总数"]
    assert any("当前" in requirement and "时间范围" in requirement for requirement in payload["requirements"])
    assert any("实体的总量" in requirement for requirement in payload["requirements"])
    assert any("严禁生成 orders.status" in requirement for requirement in payload["requirements"])


def test_build_sql_generation_payload_preserves_resolved_contract_plan() -> None:
    payload = build_sql_generation_payload(
        "销售额最高的前 5 个品类是什么？",
        _context(relationship_type="foreign_key"),
        _plan(),
        question_intent={
            "original_question": "销售额最高的前 5 个品类是什么？",
            "query_plan": {
                "entities": ["order_items", "products"],
                "measures": [{"name": "category_sales_amount", "operation": "sum"}],
                "dimensions": ["category"],
                "order_by": ["category_sales_amount DESC"],
                "limit": 5,
                "expected_row_shape": "ranking",
            },
            "resolved_contracts": [{
                "contract_key": "category_sales_ranking",
                "business_definition": "按商品品类汇总订单商品明细售价，并按销售额从高到低排行。",
                "source_tables": ["order_items", "products"],
                "source_fields": ["order_items.price", "products.category"],
                "semantic_config": {"plan": {"limit": 5, "expected_row_shape": "ranking"}},
            }],
        },
    )

    assert payload["question_intent"]["query_plan"]["order_by"] == ["category_sales_amount DESC"]
    assert payload["question_intent"]["resolved_contracts"][0]["contract_key"] == "category_sales_ranking"


def test_build_sql_generation_payload_requires_explicit_time_predicate_and_repair_rules() -> None:
    payload = build_sql_generation_payload(
        "2017年卖了多少钱？",
        _context(),
        _plan(),
        repair_context={
            "intent_errors": ["模型 SQL 未满足明确时间范围"],
            "required": {
                "time_filter": "{time_field} >= DATE '2017-01-01' AND {time_field} < DATE '2018-01-01'",
            },
            "guard_error": {
                "guard_errors": ["字段不存在或未在 schema_metadata 中登记：order_date"],
            },
        },
        question_intent={
            "query_spec": {
                "time_filter": "{time_field} >= DATE '2017-01-01' AND {time_field} < DATE '2018-01-01'",
            },
        },
    )

    assert payload["time_constraint"]["required_predicate"].startswith("{time_field} >=")
    assert any("输出别名" in rule for rule in payload["repair_rules"])
    assert any("完整时间条件" in rule for rule in payload["repair_rules"])


def test_build_sql_generation_payload_repairs_invalid_payment_status_filter() -> None:
    payload = build_sql_generation_payload(
        "当前用户总数是多少？",
        _context(),
        _plan(),
        repair_context={
            "intent_errors": [
                "模型 SQL 使用了错误支付口径：orders.status 没有 paid，请关联 payments 并使用 payments.status = 'paid'。"
            ],
        },
    )

    assert any("不得使用 orders.status = 'paid'" in rule for rule in payload["repair_rules"])
    assert any("删除支付状态过滤" in rule for rule in payload["repair_rules"])


def test_parse_model_sql_response_extracts_json_sql() -> None:
    response = ModelResponse(
        ok=True,
        content='{"sql":"SELECT o.id FROM orders o LIMIT 10","reasoning":"ok","tables":["orders"],"warnings":[]}',
        provider="local",
        model="test",
        latency_ms=12,
        usage=ModelUsage(total_tokens=20),
    )

    parsed = parse_model_sql_response(response)

    assert parsed["sql"] == "SELECT o.id FROM orders o LIMIT 10"
    assert parsed["tables"] == ["orders"]
    assert parsed["warnings"] == []


def test_parse_model_sql_response_warns_for_select_star() -> None:
    response = ModelResponse(
        ok=True,
        content='{"sql":"SELECT * FROM orders LIMIT 10"}',
        provider="local",
        model="test",
        latency_ms=1,
    )

    parsed = parse_model_sql_response(response)

    assert parsed["sql"] == "SELECT * FROM orders LIMIT 10"
    assert any("SELECT *" in warning for warning in parsed["warnings"])


def test_generate_sql_with_model_returns_generated_sql() -> None:
    adapter = FakeAdapter(
        ModelResponse(
            ok=True,
            content='{"sql":"SELECT DATE(o.created_at) AS order_date, SUM(o.total_amount) AS sales FROM orders o LIMIT 7","warnings":[]}',
            provider="local",
            model="test-model",
            latency_ms=8,
        )
    )

    result = generate_sql_with_model("最近 7 天销售额是多少？", _context(), _plan(), adapter)

    assert result.path == "model_generate"
    assert "SUM(o.total_amount)" in result.sql
    assert result.model_provider == "local"
    assert result.model_name == "test-model"
    assert adapter.requests[0].response_format == {"type": "json_object"}


def test_generate_sql_with_model_does_not_replace_model_sql_with_summary_rule() -> None:
    adapter = FakeAdapter(
        ModelResponse(
            ok=True,
            content=(
                '{"sql":"SELECT SUM(orders.total_amount) AS sales_amount, '
                'COUNT(DISTINCT orders.id) AS order_count, '
                'AVG(orders.total_amount) / COUNT(DISTINCT orders.id) AS avg_order_value '
                "FROM orders WHERE orders.status = 'paid' LIMIT 30\"}"
            ),
            provider="local",
            model="test-model",
            latency_ms=8,
        )
    )

    result = generate_sql_with_model(
        "当前数据库总销售额、订单数和客单价是多少？",
        _context(),
        _plan(),
        adapter,
    )

    assert "orders.status = 'paid'" in result.sql
    assert result.warnings == []


def test_generate_sql_with_model_returns_structured_model_error() -> None:
    adapter = FakeAdapter(
        ModelResponse(
            ok=False,
            provider="local",
            model="test-model",
            latency_ms=8,
            error_code="transport_error",
            error_message="timeout",
        )
    )

    result = generate_sql_with_model("最近 7 天销售额是多少？", _context(), _plan(), adapter)

    assert result.path == "model_error"
    assert result.sql == ""
    assert result.warnings == ["timeout"]


def test_model_generated_sql_is_still_checked_by_guard_and_validator() -> None:
    adapter = FakeAdapter(
        ModelResponse(
            ok=True,
            content='{"sql":"SELECT o.not_exists FROM orders o LIMIT 10","warnings":[]}',
            provider="local",
            model="test-model",
            latency_ms=8,
        )
    )

    context = _context()
    result = generate_sql_with_model("列出订单不存在字段", context, _plan(), adapter)
    guard = guard_sql(result.sql, schema_fields=context.fields)

    assert result.path == "model_generate"
    assert guard.allowed is False
    assert guard.errors == ["字段不存在或未在 schema_metadata 中登记：orders.not_exists"]


def _context(relationship_type: str = "id_to_foreign_key") -> RetrievalContext:
    return RetrievalContext(
        metrics=[
            MetricContext(
                metric_name="sales_amount",
                display_name="销售额",
                description="已支付订单销售额",
                formula="SUM(orders.total_amount)",
                required_tables=["orders"],
                required_fields=["orders.total_amount"],
                score=1,
            )
        ],
        schema_columns=[
            SchemaColumnContext(
                table_name="orders",
                column_name="id",
                data_type="text",
                description="orders.id",
                business_meaning="订单主键",
            ),
            SchemaColumnContext(
                table_name="orders",
                column_name="created_at",
                data_type="timestamp",
                description="orders.created_at",
                business_meaning="订单创建时间",
            ),
            SchemaColumnContext(
                table_name="orders",
                column_name="total_amount",
                data_type="numeric",
                description="orders.total_amount",
                business_meaning="订单金额",
            ),
            SchemaColumnContext(
                table_name="payments",
                column_name="order_id",
                data_type="text",
                description="payments.order_id",
                business_meaning="支付所属订单",
            ),
        ],
        table_relationships=[
            TableRelationshipContext(
                left_table="orders",
                left_column="id",
                right_table="payments",
                right_column="order_id",
                relationship_type=relationship_type,
                confidence=0.92,
                reason="payments.order_id 命名上指向 orders.id",
            )
        ],
        tables=["orders", "payments"],
        fields=["orders.id", "orders.created_at", "orders.total_amount", "payments.order_id"],
        metric_summary="销售额 = 已支付订单 total_amount 汇总",
    )


def _plan(
    path_type: str = "cold_path",
    reuse_type: str = "regenerate",
    selected_sql: str | None = None,
) -> SqlReusePlan:
    return SqlReusePlan(
        path_type=path_type,
        reuse_type=reuse_type,
        memory_hit=False,
        candidate_count=0,
        selected_sql=selected_sql,
    )
