"""第二轮编排优化回归测试：并行预取（2b）、修复上下文瘦身（2c）、取消令牌（2d）、取值样本（3b-lite）。"""
import threading
import time

import pytest

from backend.app.core.config import settings
from backend.app.agents import analysis_graph
from backend.app.schemas.memories import SqlReusePlan
from backend.app.schemas.retrieval import (
    MetricContext,
    RetrievalContext,
    SchemaColumnContext,
    TableRelationshipContext,
)
from backend.app.services import analysis_prep
from backend.app.services.agent_service import AnalysisCancelledError
from backend.app.tools.context_builder import build_retrieval_context
from backend.app.tools.model_sql_generator import build_sql_generation_payload


# ---------------------------------------------------------------------------
# 2b：意图解析与检索并行
# ---------------------------------------------------------------------------


def test_prepare_analysis_inputs_runs_intent_and_retrieval_concurrently(monkeypatch) -> None:
    monkeypatch.setattr(settings, "parallel_intent_retrieval", True)
    delay = 0.25

    def slow_intent(question, conversation_context=""):
        time.sleep(delay)
        from backend.app.tools.question_intent_parser import parse_question_intent

        return parse_question_intent.__wrapped__(question) if hasattr(
            parse_question_intent, "__wrapped__"
        ) else _fake_intent(question)

    def _fake_intent(question):
        from backend.app.schemas.analysis import PathType  # noqa: F401
        from backend.app.tools.question_intent_parser import ParsedQuestionIntent

        return ParsedQuestionIntent(original_question=question, normalized_question=question)

    def slow_preretrieve(question):
        time.sleep(delay)
        return analysis_prep.PrecomputedRetrieval(question_vector=[0.1], metrics=[], schema_columns=[])

    monkeypatch.setattr(analysis_prep, "parse_question_intent", lambda q, conversation_context="": (time.sleep(delay), _fake_intent(q))[1])
    monkeypatch.setattr(analysis_prep, "_preretrieve", slow_preretrieve)

    started = time.perf_counter()
    intent, precomputed = analysis_prep.prepare_analysis_inputs("测试问题")
    elapsed = time.perf_counter() - started

    assert intent is not None
    assert precomputed is not None and precomputed.question_vector == [0.1]
    assert elapsed < delay * 1.8, f"两个 {delay}s 任务应并行完成，实际 {elapsed:.2f}s"


def test_prepare_analysis_inputs_survives_retrieval_failure(monkeypatch) -> None:
    monkeypatch.setattr(settings, "parallel_intent_retrieval", True)

    def _fake_intent(question):
        from backend.app.tools.question_intent_parser import ParsedQuestionIntent

        return ParsedQuestionIntent(original_question=question, normalized_question=question)

    monkeypatch.setattr(analysis_prep, "parse_question_intent", lambda q, conversation_context="": _fake_intent(q))
    monkeypatch.setattr(
        analysis_prep, "_preretrieve", lambda q: (_ for _ in ()).throw(RuntimeError("embedding down"))
    )

    intent, precomputed = analysis_prep.prepare_analysis_inputs("测试问题")
    assert intent is not None
    assert precomputed is None, "检索预取失败应回退 None，由图内串行检索兜底"


def test_precomputed_context_produces_same_tables_as_direct_retrieval() -> None:
    question = "最近 30 天销售额按天变化如何？"
    direct = build_retrieval_context(question)
    precomputed = analysis_prep._preretrieve(question)
    reused = build_retrieval_context(
        question,
        question_vector=precomputed.question_vector,
        precomputed_metrics=precomputed.metrics,
        precomputed_schema=precomputed.schema_columns,
    )
    assert sorted(reused.tables) == sorted(direct.tables)
    assert {f"{c.table_name}.{c.column_name}" for c in reused.schema_columns} == {
        f"{c.table_name}.{c.column_name}" for c in direct.schema_columns
    }


# ---------------------------------------------------------------------------
# 2d：取消令牌
# ---------------------------------------------------------------------------


def test_cancelled_event_stops_graph_nodes_immediately() -> None:
    cancel_event = threading.Event()
    cancel_event.set()
    state = {"cancel_event": cancel_event, "question": "q", "node_timings": {}}
    with pytest.raises(AnalysisCancelledError):
        analysis_graph._retrieve_context_node(state)
    with pytest.raises(AnalysisCancelledError):
        analysis_graph._generate_model_sql_node(state)
    with pytest.raises(AnalysisCancelledError):
        analysis_graph._execute_sql_node(state)


def test_unset_cancel_event_does_not_interfere() -> None:
    state = {"cancel_event": threading.Event(), "node_timings": {}}
    analysis_graph._raise_if_cancelled(state)  # 不应抛出
    analysis_graph._raise_if_cancelled({})  # 无事件同样安全


# ---------------------------------------------------------------------------
# 3b-lite：低基数列真实取值样本
# ---------------------------------------------------------------------------


def test_context_attaches_real_sample_values_for_enum_columns() -> None:
    context = build_retrieval_context("各支付方式的支付成功率是多少？")
    status_columns = [
        column
        for column in context.schema_columns
        if column.table_name == "payments" and column.column_name == "status"
    ]
    assert status_columns, "payments.status 应该被召回"
    assert "paid" in status_columns[0].sample_values, (
        f"应包含数据库真实取值，实际: {status_columns[0].sample_values}"
    )


def test_payload_includes_sample_values_and_rule() -> None:
    context = RetrievalContext(
        metrics=[],
        schema_columns=[
            SchemaColumnContext(
                table_name="payments", column_name="status", data_type="text",
                description="支付状态", business_meaning="支付状态",
                sample_values=["failed", "paid"],
            )
        ],
        tables=["payments"],
        fields=["payments.status"],
    )
    payload = build_sql_generation_payload("支付成功率", context, SqlReusePlan())
    field_entry = payload["schema_fields"][0]
    assert field_entry["values"] == ["failed", "paid"]
    assert any("真实取值样本" in rule for rule in payload["requirements"])


# ---------------------------------------------------------------------------
# 2c：修复上下文瘦身
# ---------------------------------------------------------------------------


def _wide_context() -> RetrievalContext:
    def column(table, name):
        return SchemaColumnContext(
            table_name=table, column_name=name, data_type="text",
            description=f"{table}.{name}", business_meaning="",
        )

    return RetrievalContext(
        metrics=[
            MetricContext(
                metric_name="sales_amount", display_name="销售额", description="d",
                formula="SUM(orders.total_amount)", required_tables=["orders"],
                required_fields=["orders.total_amount"], score=1,
            )
        ],
        schema_columns=[
            column("orders", "id"), column("orders", "total_amount"),
            column("payments", "status"), column("products", "category"),
            column("traffic_events", "source"), column("coupons", "code"),
        ],
        table_relationships=[
            TableRelationshipContext(
                left_table="orders", left_column="id", right_table="payments",
                right_column="order_id", relationship_type="foreign_key",
                confidence=0.98, reason="fk",
            ),
            TableRelationshipContext(
                left_table="orders", left_column="id", right_table="coupons",
                right_column="order_id", relationship_type="same_key",
                confidence=0.8, reason="key",
            ),
        ],
        tables=["orders", "payments", "products", "traffic_events", "coupons"],
        fields=[],
    )


def test_repair_payload_keeps_only_relevant_tables() -> None:
    context = _wide_context()
    payload = build_sql_generation_payload(
        "销售额",
        context,
        SqlReusePlan(),
        repair_context={
            "previous_sql": "SELECT SUM(o.total_amount) FROM orders o JOIN payments p ON p.order_id = o.id",
            "intent_errors": ["时间范围缺失"],
        },
        question_intent={"query_plan": {"entities": ["orders", "payments"]}},
    )
    field_tables = {item["table"] for item in payload["schema_fields"]}
    assert field_tables == {"orders", "payments"}, f"修复载荷应只保留相关表: {field_tables}"
    for relationship in payload["table_relationships"]:
        assert "coupons" not in relationship["left"] and "coupons" not in relationship["right"]


def test_generation_payload_keeps_full_context_without_repair() -> None:
    context = _wide_context()
    payload = build_sql_generation_payload("销售额", context, SqlReusePlan())
    field_tables = {item["table"] for item in payload["schema_fields"]}
    assert "traffic_events" in field_tables and "coupons" in field_tables
