from backend.app.agents.analysis_graph import _context_table_coverage, _select_generated_sql
from backend.app.core.model_adapter import ModelResponse
from backend.app.schemas.memories import SqlReusePlan
from backend.app.schemas.retrieval import MetricContext, RetrievalContext, SchemaColumnContext


class FakeAdapter:
    def __init__(self, response: ModelResponse):
        self.response = response
        self.calls = 0

    def chat(self, request):
        self.calls += 1
        return self.response


def test_select_generated_sql_uses_deterministic_path_when_model_disabled() -> None:
    adapter = FakeAdapter(
        ModelResponse(
            ok=True,
            content='{"sql":"SELECT 1"}',
            provider="local",
            model="test",
            latency_ms=1,
        )
    )

    result = _select_generated_sql(
        question="最近 7 天销售额是多少？",
        retrieval_context=_context(),
        reuse_plan=_plan("cold_path"),
        adapter=adapter,
        model_enabled=False,
    )

    assert result.path == "template_render"
    assert "orders" in result.sql
    assert adapter.calls == 0


def test_select_generated_sql_uses_model_for_enabled_cold_path() -> None:
    adapter = FakeAdapter(
        ModelResponse(
            ok=True,
            content='{"sql":"SELECT o.id FROM orders o LIMIT 10","warnings":[]}',
            provider="local",
            model="test",
            latency_ms=1,
        )
    )

    result = _select_generated_sql(
        question="列出订单",
        retrieval_context=_context(),
        reuse_plan=_plan("cold_path"),
        adapter=adapter,
        model_enabled=True,
    )

    assert result.path == "model_generate"
    assert result.sql == "SELECT o.id FROM orders o LIMIT 10"
    assert adapter.calls == 1


def test_select_generated_sql_falls_back_when_model_returns_no_sql() -> None:
    adapter = FakeAdapter(
        ModelResponse(
            ok=False,
            provider="local",
            model="test",
            latency_ms=1,
            error_message="timeout",
        )
    )

    result = _select_generated_sql(
        question="最近 7 天销售额是多少？",
        retrieval_context=_context(),
        reuse_plan=_plan("cold_path"),
        adapter=adapter,
        model_enabled=True,
    )

    assert result.path == "template_render"
    assert "orders" in result.sql
    assert any("回退到确定性生成路径" in warning for warning in result.warnings)


def test_select_generated_sql_does_not_use_model_for_rewrite_path() -> None:
    adapter = FakeAdapter(
        ModelResponse(
            ok=True,
            content='{"sql":"SELECT 1"}',
            provider="local",
            model="test",
            latency_ms=1,
        )
    )

    result = _select_generated_sql(
        question="最近 90 天每月订单数是多少？",
        retrieval_context=_context(),
        reuse_plan=_plan("rewrite_path"),
        adapter=adapter,
        model_enabled=True,
    )

    assert result.path == "deterministic_rewrite"
    assert adapter.calls == 0


def test_select_generated_sql_warns_when_context_table_is_missing_with_model_disabled() -> None:
    adapter = FakeAdapter(
        ModelResponse(
            ok=True,
            content='{"sql":"SELECT source FROM traffic_events LIMIT 10"}',
            provider="local",
            model="test",
            latency_ms=1,
        )
    )

    result = _select_generated_sql(
        question="按流量来源统计访问到下单的转化率",
        retrieval_context=_context_with_extra_table("traffic_events"),
        reuse_plan=_plan("rewrite_path"),
        adapter=adapter,
        model_enabled=False,
    )

    assert result.path == "deterministic_rewrite"
    assert "traffic_events" not in result.sql
    assert any("关键上下文表" in warning for warning in result.warnings)
    assert adapter.calls == 0


def test_select_generated_sql_uses_model_when_rewrite_misses_context_table() -> None:
    adapter = FakeAdapter(
        ModelResponse(
            ok=True,
            content='{"sql":"SELECT source, COUNT(*) AS visits FROM traffic_events GROUP BY source LIMIT 10","warnings":[]}',
            provider="local",
            model="test",
            latency_ms=1,
        )
    )

    result = _select_generated_sql(
        question="按流量来源统计访问到下单的转化率",
        retrieval_context=_context_with_extra_table("traffic_events"),
        reuse_plan=_plan("rewrite_path"),
        adapter=adapter,
        model_enabled=True,
    )

    assert result.path == "model_generate"
    assert "traffic_events" in result.sql
    assert any("关键上下文表" in warning for warning in result.warnings)
    assert adapter.calls == 1


def test_context_table_coverage_reports_missing_non_default_tables() -> None:
    coverage = _context_table_coverage(
        "SELECT COUNT(*) FROM orders LIMIT 10",
        ["orders", "payments", "traffic_events"],
    )

    assert coverage == {
        "required_tables": ["traffic_events"],
        "sql_tables": ["orders"],
        "missing_tables": ["traffic_events"],
        "covered": False,
    }


def _plan(path_type: str) -> SqlReusePlan:
    return SqlReusePlan(
        path_type=path_type,
        reuse_type="regenerate",
        memory_hit=False,
        candidate_count=0,
    )


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
                column_name="id",
                data_type="text",
                description="orders.id",
                business_meaning="订单 ID",
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
        fields=["orders.id", "orders.total_amount"],
        metric_summary="销售额 = 已支付订单 total_amount 汇总",
    )


def _context_with_extra_table(table_name: str) -> RetrievalContext:
    context = _context()
    return context.model_copy(
        update={
            "schema_columns": [
                *context.schema_columns,
                SchemaColumnContext(
                    table_name=table_name,
                    column_name="source",
                    data_type="text",
                    description=f"{table_name}.source",
                    business_meaning="流量来源",
                ),
            ],
            "tables": [*context.tables, table_name],
            "fields": [*context.fields, f"{table_name}.source"],
        }
    )
