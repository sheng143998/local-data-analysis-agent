import json

from backend.app.agents.analysis_graph import (
    _context_table_coverage,
    _repair_model_sql_node,
    _route_memory_candidate,
    _route_execution_result,
    _route_generated_sql_intent,
    _route_verified_memory_sql,
    _select_generated_sql,
    _validate_generated_sql_intent_node,
    _verify_generated_sql_intent,
    _verify_memory_sql,
    run_analysis_graph,
)
from backend.app.core.model_adapter import ModelResponse
from backend.app.tools.question_intent_parser import ParsedQuestionIntent
from backend.app.schemas.memories import SqlReusePlan
from backend.app.schemas.retrieval import MetricContext, RetrievalContext, SchemaColumnContext
from backend.app.schemas.sql_execution import SqlExecutionResult
from backend.app.schemas.sql_generation import GeneratedSql
from backend.app.schemas.sql_validation import SqlGuardResult


class FakeAdapter:
    def __init__(self, response: ModelResponse):
        self.response = response
        self.calls = 0
        self.last_request = None

    def chat(self, request):
        self.calls += 1
        self.last_request = request
        return self.response


def test_run_analysis_graph_returns_clarification_for_uncertain_intent(monkeypatch) -> None:
    def fake_parse(question):
        return ParsedQuestionIntent(
            original_question=question,
            normalized_question="查看最近业务情况",
            confidence=0.3,
            needs_clarification=True,
            clarification="我理解你想查看最近的核心经营概览。是否查询销售额、订单数和客单价，还是需要修改？",
            source="llm",
        )

    monkeypatch.setattr("backend.app.agents.analysis_graph.parse_question_intent", fake_parse)

    response = run_analysis_graph("看看最近情况")

    assert response.sql == ""
    assert response.rows == []
    assert "是否查询" in response.summary
    assert response.source.security == "未生成 SQL，等待用户确认"


def test_route_memory_candidate_verifies_existing_memory_sql() -> None:
    route = _route_memory_candidate(
        {
            "reuse_plan": SqlReusePlan(
                path_type="fast_path",
                reuse_type="direct_reuse",
                memory_hit=True,
                selected_sql="SELECT id FROM orders LIMIT 10",
                candidate_count=1,
            )
        }
    )

    assert route == "verify_memory_sql"


def test_route_memory_candidate_uses_model_without_candidate_sql() -> None:
    route = _route_memory_candidate(
        {
            "reuse_plan": SqlReusePlan(
                path_type="rewrite_path",
                reuse_type="regenerate",
                memory_hit=True,
                candidate_count=1,
            )
        }
    )

    assert route == "generate_model_sql"


def test_route_verified_memory_sql_reuses_only_after_verification() -> None:
    assert _route_verified_memory_sql({"memory_verification": {"decision": "reuse"}}) == "guard_sql"
    assert (
        _route_verified_memory_sql({"memory_verification": {"decision": "rewrite"}})
        == "generate_model_sql"
    )


def test_route_generated_sql_intent_repairs_once_before_guard() -> None:
    assert _route_generated_sql_intent({"sql_intent_verification": {"decision": "accept"}}) == "guard_sql"
    assert (
        _route_generated_sql_intent(
            {
                "sql_intent_verification": {"decision": "reject"},
                "selected_sql": "SELECT COUNT(*) FROM orders LIMIT 10",
                "repair_attempts": 0,
            }
        )
        == "repair_model_sql"
    )
    assert (
        _route_generated_sql_intent(
            {
                "sql_intent_verification": {"decision": "reject"},
                "selected_sql": "SELECT COUNT(*) FROM orders LIMIT 10",
                "repair_attempts": 1,
            }
        )
        == "guard_sql"
    )


def test_route_execution_result_repairs_runtime_error_once() -> None:
    assert (
        _route_execution_result(
            {
                "execution": SqlExecutionResult(status="error", error_message="column x does not exist"),
                "selected_sql": "SELECT x FROM orders LIMIT 10",
                "execution_repair_attempts": 0,
            }
        )
        == "repair_model_sql"
    )
    assert (
        _route_execution_result(
            {
                "execution": SqlExecutionResult(status="error", error_message="column x does not exist"),
                "selected_sql": "SELECT x FROM orders LIMIT 10",
                "execution_repair_attempts": 1,
            }
        )
        == "update_memory"
    )
    assert _route_execution_result({"execution": SqlExecutionResult(status="success")}) == "update_memory"


def test_route_execution_result_repairs_guard_block_once() -> None:
    assert (
        _route_execution_result(
            {
                "execution": SqlExecutionResult(
                    status="blocked",
                    error_message="SQL Guard 未放行，Executor 拒绝执行",
                    error_category="guard_blocked",
                ),
                "selected_sql": "SELECT missing_alias.amount FROM orders LIMIT 10",
                "execution_repair_attempts": 0,
            }
        )
        == "repair_model_sql"
    )
    assert (
        _route_execution_result(
            {
                "execution": SqlExecutionResult(
                    status="blocked",
                    error_message="SQL Guard 未放行，Executor 拒绝执行",
                    error_category="guard_blocked",
                ),
                "selected_sql": "SELECT missing_alias.amount FROM orders LIMIT 10",
                "execution_repair_attempts": 1,
            }
        )
        == "update_memory"
    )


def test_verify_memory_sql_allows_matching_fast_path_sql() -> None:
    verification = _verify_memory_sql(
        question="最近 7 天销售额是多少？",
        retrieval_context=_context(),
        reuse_plan=_plan("fast_path", score=0.91),
        sql="SELECT SUM(o.total_amount) AS total_amount FROM orders o LIMIT 10",
    )

    assert verification["decision"] == "reuse"
    assert verification["warnings"] == []


def test_verify_memory_sql_rewrites_when_metric_does_not_match() -> None:
    verification = _verify_memory_sql(
        question="最近 7 天订单数是多少？",
        retrieval_context=_context(),
        reuse_plan=_plan("fast_path", score=0.91),
        sql="SELECT SUM(o.total_amount) AS total_amount FROM orders o LIMIT 10",
    )

    assert verification["decision"] == "rewrite"
    assert any("order_count" in warning for warning in verification["warnings"])


def test_verify_memory_sql_rewrites_non_fast_candidate() -> None:
    verification = _verify_memory_sql(
        question="最近 7 天销售额是多少？",
        retrieval_context=_context(),
        reuse_plan=_plan("rewrite_path", score=0.75),
        sql="SELECT SUM(o.total_amount) AS total_amount FROM orders o LIMIT 10",
    )

    assert verification["decision"] == "rewrite"
    assert any("未达到 fast_path" in warning for warning in verification["warnings"])


def test_verify_generated_sql_intent_rejects_metric_mismatch() -> None:
    verification = _verify_generated_sql_intent(
        question="最近 7 天订单数是多少？",
        retrieval_context=_context(),
        sql="SELECT SUM(o.total_amount) AS total_amount FROM orders o LIMIT 10",
    )

    assert verification["decision"] == "reject"
    assert any("order_count" in warning for warning in verification["warnings"])


def test_validate_generated_sql_intent_accepts_matching_model_sql() -> None:
    state = _validate_generated_sql_intent_node(
        {
            "question": "最近 7 天销售额是多少？",
            "retrieval_context": _context(),
            "generated_sql": GeneratedSql(
                path="model_generate",
                sql="SELECT SUM(o.total_amount) AS total_amount FROM orders o LIMIT 10",
            ),
            "selected_sql": "SELECT SUM(o.total_amount) AS total_amount FROM orders o LIMIT 10",
            "repair_attempts": 0,
        }
    )

    assert state["sql_intent_verification"]["decision"] == "accept"
    assert state["generated_sql"].path == "model_generate"


def test_validate_generated_sql_intent_blocks_after_failed_repair() -> None:
    state = _validate_generated_sql_intent_node(
        {
            "question": "最近 7 天订单数是多少？",
            "retrieval_context": _context(),
            "generated_sql": GeneratedSql(
                path="model_repair",
                sql="SELECT SUM(o.total_amount) AS total_amount FROM orders o LIMIT 10",
            ),
            "selected_sql": "SELECT SUM(o.total_amount) AS total_amount FROM orders o LIMIT 10",
            "repair_attempts": 1,
        }
    )

    assert state["sql_intent_verification"]["decision"] == "reject"
    assert state["generated_sql"].path == "model_error"
    assert state["selected_sql"] == ""


def test_repair_model_sql_node_sends_intent_errors_to_model() -> None:
    adapter = FakeAdapter(
        ModelResponse(
            ok=True,
            content='{"sql":"SELECT COUNT(DISTINCT o.id) AS order_count FROM orders o LIMIT 10","warnings":[]}',
            provider="local",
            model="test",
            latency_ms=1,
        )
    )

    state = _repair_model_sql_node(
        {
            "question": "最近 7 天订单数是多少？",
            "retrieval_context": _context(),
            "reuse_plan": _plan("cold_path"),
            "generated_sql": GeneratedSql(
                path="model_generate",
                sql="SELECT SUM(o.total_amount) AS total_amount FROM orders o LIMIT 10",
            ),
            "selected_sql": "SELECT SUM(o.total_amount) AS total_amount FROM orders o LIMIT 10",
            "sql_intent_verification": {
                "decision": "reject",
                "warnings": ["模型 SQL 缺少当前问题需要的指标口径：order_count"],
                "required": {"required_metric_tokens": ["order_count"]},
                "observed": {},
            },
            "repair_attempts": 0,
            "_test_adapter": adapter,
        }
    )

    assert state["generated_sql"].path == "model_repair"
    assert "order_count" in state["selected_sql"]
    assert state["repair_attempts"] == 1
    user_payload = json.loads(adapter.last_request.messages[1].content)
    assert user_payload["repair_context"]["intent_errors"]


def test_repair_model_sql_node_sends_execution_error_to_model() -> None:
    adapter = FakeAdapter(
        ModelResponse(
            ok=True,
            content='{"sql":"SELECT o.id FROM orders o LIMIT 10","warnings":[]}',
            provider="local",
            model="test",
            latency_ms=1,
        )
    )

    state = _repair_model_sql_node(
        {
            "question": "列出订单",
            "retrieval_context": _context(),
            "reuse_plan": _plan("cold_path"),
            "generated_sql": GeneratedSql(
                path="model_generate",
                sql="SELECT missing_column FROM orders LIMIT 10",
            ),
            "selected_sql": "SELECT missing_column FROM orders LIMIT 10",
            "sql_intent_verification": {"decision": "accept", "warnings": []},
            "guard": SqlGuardResult(
                allowed=True,
                final_sql="SELECT missing_column FROM orders LIMIT 10",
            ),
            "execution": SqlExecutionResult(
                status="error",
                error_message='column "missing_column" does not exist',
                error_category="missing_column",
                user_error_message="SQL 使用了当前数据表中不存在的字段，我会尝试改用已登记的字段。",
            ),
            "repair_attempts": 0,
            "execution_repair_attempts": 0,
            "_test_adapter": adapter,
        }
    )

    assert state["generated_sql"].path == "model_repair"
    assert state["selected_sql"] == "SELECT o.id FROM orders o LIMIT 10"
    assert state["execution_repair_attempts"] == 1
    user_payload = json.loads(adapter.last_request.messages[1].content)
    execution_error = user_payload["repair_context"]["execution_error"]
    assert execution_error["category"] == "missing_column"
    assert "missing_column" in execution_error["message"]


def test_repair_model_sql_node_sends_guard_error_to_model() -> None:
    adapter = FakeAdapter(
        ModelResponse(
            ok=True,
            content='{"sql":"SELECT o.id FROM orders o LIMIT 10","warnings":[]}',
            provider="local",
            model="test",
            latency_ms=1,
        )
    )

    state = _repair_model_sql_node(
        {
            "question": "列出订单",
            "retrieval_context": _context(),
            "reuse_plan": _plan("cold_path"),
            "generated_sql": GeneratedSql(
                path="model_generate",
                sql="SELECT missing_alias.amount FROM orders LIMIT 10",
            ),
            "selected_sql": "SELECT missing_alias.amount FROM orders LIMIT 10",
            "sql_intent_verification": {"decision": "accept", "warnings": []},
            "guard": SqlGuardResult(
                allowed=False,
                errors=["字段不存在或未在 schema_metadata 中登记：missing_alias.amount"],
            ),
            "execution": SqlExecutionResult(
                status="blocked",
                error_message="SQL Guard 未放行，Executor 拒绝执行",
                error_category="guard_blocked",
                user_error_message="这条查询没有通过只读安全校验，因此没有执行。",
            ),
            "repair_attempts": 0,
            "execution_repair_attempts": 0,
            "_test_adapter": adapter,
        }
    )

    assert state["generated_sql"].path == "model_repair"
    assert state["execution_repair_attempts"] == 1
    user_payload = json.loads(adapter.last_request.messages[1].content)
    guard_error = user_payload["repair_context"]["guard_error"]
    assert guard_error["category"] == "guard_blocked"
    assert guard_error["guard_errors"]


def test_select_generated_sql_returns_error_when_model_disabled() -> None:
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

    assert result.path == "model_error"
    assert result.sql == ""
    assert "fixed template main path has been removed" in result.warnings[0]
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


def test_select_generated_sql_does_not_fallback_when_model_returns_no_sql() -> None:
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

    assert result.path == "model_error"
    assert result.sql == ""
    assert any("fixed template generation is no longer used" in warning for warning in result.warnings)
    assert adapter.calls == 1


def test_select_generated_sql_uses_model_for_rewrite_path() -> None:
    adapter = FakeAdapter(
        ModelResponse(
            ok=True,
            content='{"sql":"SELECT date_trunc(''month'', paid_at) AS month, COUNT(*) AS orders FROM orders GROUP BY 1 LIMIT 12"}',
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

    assert result.path == "model_rewrite"
    assert "orders" in result.sql
    assert adapter.calls == 1


def test_select_generated_sql_warns_when_model_misses_context_table() -> None:
    adapter = FakeAdapter(
        ModelResponse(
            ok=True,
            content='{"sql":"SELECT COUNT(*) AS orders FROM orders LIMIT 10","warnings":[]}',
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

    assert result.path == "model_rewrite"
    assert "traffic_events" not in result.sql
    assert any("traffic_events" in warning for warning in result.warnings)
    assert adapter.calls == 1


def test_select_generated_sql_keeps_model_sql_when_context_table_is_covered() -> None:
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

    assert result.path == "model_rewrite"
    assert "traffic_events" in result.sql
    assert result.warnings == []
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


def test_context_table_coverage_does_not_require_recalled_users_table() -> None:
    coverage = _context_table_coverage(
        "SELECT COUNT(*) AS orders FROM orders LIMIT 10",
        ["orders", "payments", "users"],
    )

    assert coverage == {
        "required_tables": [],
        "sql_tables": ["orders"],
        "missing_tables": [],
        "covered": True,
    }


def test_verify_generated_sql_intent_accepts_current_overall_summary_without_order_by() -> None:
    verification = _verify_generated_sql_intent(
        question="当前数据库总销售额、订单数和客单价是多少？",
        retrieval_context=_context_with_extra_table("users"),
        sql=(
            "SELECT COUNT(*) AS order_count, "
            "SUM(total_amount) AS total_amount, "
            "ROUND(SUM(total_amount) / NULLIF(COUNT(*), 0), 2) AS avg_order_value "
            "FROM orders WHERE total_amount > 0 LIMIT 1"
        ),
    )

    assert verification["decision"] == "accept"
    assert verification["warnings"] == []


def test_verify_generated_sql_intent_rejects_orders_status_paid_filter() -> None:
    verification = _verify_generated_sql_intent(
        question="当前数据库总销售额、订单数和客单价是多少？",
        retrieval_context=_context_with_extra_table("users"),
        sql=(
            "SELECT SUM(o.total_amount) AS sales_amount, COUNT(DISTINCT o.id) AS order_count "
            "FROM orders o WHERE o.status = 'paid' LIMIT 1"
        ),
    )

    assert verification["decision"] == "reject"
    assert any("payments.status" in warning for warning in verification["warnings"])


def _plan(path_type: str, score: float = 0) -> SqlReusePlan:
    return SqlReusePlan(
        path_type=path_type,
        reuse_type="regenerate",
        memory_hit=False,
        candidate_count=0,
        score=score,
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
