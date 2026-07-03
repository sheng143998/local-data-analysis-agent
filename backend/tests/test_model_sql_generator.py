from backend.app.core.model_adapter import ModelResponse, ModelUsage
from backend.app.schemas.memories import SqlReusePlan
from backend.app.schemas.retrieval import MetricContext, RetrievalContext, SchemaColumnContext
from backend.app.tools.model_sql_generator import (
    build_sql_generation_messages,
    generate_sql_with_model,
    parse_model_sql_response,
)


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
    assert "metric_definitions" not in messages[1].content


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


def _context() -> RetrievalContext:
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
        ],
        tables=["orders"],
        fields=["orders.created_at", "orders.total_amount"],
        metric_summary="销售额 = 已支付订单 total_amount 汇总",
    )


def _plan() -> SqlReusePlan:
    return SqlReusePlan(
        path_type="cold_path",
        reuse_type="regenerate",
        memory_hit=False,
        candidate_count=0,
    )
