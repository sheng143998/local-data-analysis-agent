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
