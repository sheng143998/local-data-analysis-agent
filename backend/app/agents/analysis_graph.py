from functools import lru_cache
import re
from time import perf_counter
from typing import Any, TypedDict
from uuid import UUID

from langgraph.graph import END, StateGraph
from sqlglot import exp, parse_one
from sqlglot.errors import ParseError

from backend.app.core.config import settings
from backend.app.core.model_adapter import ModelAdapter
from backend.app.schemas.analysis import AnalyzeResponse
from backend.app.schemas.retrieval import RetrievalContext
from backend.app.schemas.sql_generation import GeneratedSql
from backend.app.schemas.memories import SqlReusePlan
from backend.app.schemas.query_spec import QuerySpec
from backend.app.schemas.sql_execution import SqlExecutionResult
from backend.app.schemas.sql_validation import SqlGuardResult
from backend.app.tools.analysis_presenter import present_clarification_response, present_sales_trend_result
from backend.app.tools.context_builder import build_retrieval_context
from backend.app.tools.model_sql_generator import generate_sql_with_model
from backend.app.tools.question_intent_parser import ParsedQuestionIntent, parse_question_intent
from backend.app.tools.run_logger import QueryRunLogger
from backend.app.tools.sql_memory_tools import (
    plan_sql_reuse,
    retrieve_sql_memory,
    upsert_successful_sql_memory,
)
from backend.app.tools.sql_execution_tools import execute_guarded_sql
from backend.app.tools.sql_validation_tools import guard_sql
from backend.app.tools.sql_inspector import inspect_query_plan

BASE_TRANSACTION_TABLES = {
    "orders",
    "payments",
    "order_items",
    "products",
    "users",
    "refunds",
    "product_costs",
}


class AnalysisGraphState(TypedDict, total=False):
    question: str
    app_user_id: UUID | None
    original_question: str
    question_intent: dict[str, Any]
    node_timings: dict[str, int]
    started: float
    retrieval_context: RetrievalContext
    metric_names: list[str]
    memory_candidates: list[Any]
    reuse_plan: SqlReusePlan
    memory_verification: dict[str, Any]
    sql_intent_verification: dict[str, Any]
    repair_attempts: int
    execution_repair_attempts: int
    generated_sql: GeneratedSql
    selected_sql: str
    guard: SqlGuardResult
    execution: SqlExecutionResult
    latency_ms: int
    updated_memory_id: Any
    response: AnalyzeResponse


def _build_analysis_graph():
    graph = StateGraph(AnalysisGraphState)
    graph.add_node("retrieve_context", _retrieve_context_node)
    graph.add_node("plan_memory_reuse", _plan_memory_reuse_node)
    graph.add_node("verify_memory_sql", _verify_memory_sql_node)
    graph.add_node("generate_model_sql", _generate_model_sql_node)
    graph.add_node("validate_generated_sql_intent", _validate_generated_sql_intent_node)
    graph.add_node("repair_model_sql", _repair_model_sql_node)
    graph.add_node("guard_sql", _guard_sql_node)
    graph.add_node("execute_sql", _execute_sql_node)
    graph.add_node("update_memory", _update_memory_node)
    graph.add_node("present_result", _present_result_node)
    graph.add_node("log_run", _log_run_node)

    graph.set_entry_point("retrieve_context")
    graph.add_edge("retrieve_context", "plan_memory_reuse")
    graph.add_conditional_edges(
        "plan_memory_reuse",
        _route_memory_candidate,
        {"verify_memory_sql": "verify_memory_sql", "generate_model_sql": "generate_model_sql"},
    )
    graph.add_conditional_edges(
        "verify_memory_sql",
        _route_verified_memory_sql,
        {"guard_sql": "guard_sql", "generate_model_sql": "generate_model_sql"},
    )
    graph.add_edge("generate_model_sql", "validate_generated_sql_intent")
    graph.add_conditional_edges(
        "validate_generated_sql_intent",
        _route_generated_sql_intent,
        {"guard_sql": "guard_sql", "repair_model_sql": "repair_model_sql"},
    )
    graph.add_edge("repair_model_sql", "validate_generated_sql_intent")
    graph.add_edge("guard_sql", "execute_sql")
    graph.add_conditional_edges(
        "execute_sql",
        _route_execution_result,
        {"repair_model_sql": "repair_model_sql", "update_memory": "update_memory"},
    )
    graph.add_edge("update_memory", "present_result")
    graph.add_edge("present_result", "log_run")
    graph.add_edge("log_run", END)
    return graph.compile()


def run_analysis_graph(
    question: str,
    app_user_id: UUID | None = None,
    parsed_intent: ParsedQuestionIntent | None = None,
) -> AnalyzeResponse:
    """正式 LangGraph 编排：召回、记忆复用、SQL 生成、Guard、执行、呈现和日志。"""
    started = perf_counter()
    intent = parsed_intent or parse_question_intent(question)
    latency_ms = int((perf_counter() - started) * 1000)
    if intent.needs_clarification:
        return present_clarification_response(question, intent, latency_ms)

    effective_question = intent.normalized_question or question
    final_state = _analysis_graph().invoke(
        {
            "question": effective_question,
            "app_user_id": app_user_id,
            "original_question": question,
            "question_intent": intent.model_dump(),
            "node_timings": {"intent_parse": latency_ms},
            "started": started,
        }
    )
    response = final_state["response"]
    if response.question != question:
        return response.model_copy(update={"question": question})
    return response


@lru_cache(maxsize=1)
def _analysis_graph():
    return _build_analysis_graph()


def _add_node_timing(state: AnalysisGraphState, node_name: str, started: float) -> dict[str, int]:
    timings = dict(state.get("node_timings", {}))
    timings[node_name] = int((perf_counter() - started) * 1000)
    return timings


def _slowest_node(timings: dict[str, int]) -> dict[str, Any]:
    if not timings:
        return {}
    name, latency_ms = max(timings.items(), key=lambda item: item[1])
    return {"name": name, "latency_ms": latency_ms}


def _retrieve_context_node(state: AnalysisGraphState) -> AnalysisGraphState:
    started = perf_counter()
    question = state["question"]
    retrieval_context = build_retrieval_context(
        question,
        semantic_contracts=state.get("question_intent", {}).get("resolved_contracts", []),
        query_plan=state.get("question_intent", {}).get("query_plan", {}),
    )
    metric_names = [metric.metric_name for metric in retrieval_context.metrics]
    return {
        "retrieval_context": retrieval_context,
        "metric_names": metric_names,
        "node_timings": _add_node_timing(state, "context_retrieval", started),
    }


def _plan_memory_reuse_node(state: AnalysisGraphState) -> AnalysisGraphState:
    started = perf_counter()
    question = state["question"]
    retrieval_context = state["retrieval_context"]
    metric_names = state["metric_names"]
    query_spec = _query_spec_from_intent(state.get("question_intent"))
    memory_candidates = retrieve_sql_memory(
        question,
        metrics=query_spec.metrics if query_spec else metric_names,
        tables=sorted(set(retrieval_context.tables) | set(query_spec.required_tables if query_spec else [])),
        required_tables=query_spec.required_tables if query_spec else None,
    )
    reuse_plan = plan_sql_reuse(memory_candidates)
    return {
        "memory_candidates": memory_candidates,
        "reuse_plan": reuse_plan,
        "node_timings": _add_node_timing(state, "memory_retrieval_and_plan", started),
    }


def _route_memory_candidate(state: AnalysisGraphState) -> str:
    reuse_plan = state["reuse_plan"]
    if reuse_plan.selected_sql:
        return "verify_memory_sql"
    return "generate_model_sql"


def _route_verified_memory_sql(state: AnalysisGraphState) -> str:
    verification = state.get("memory_verification", {})
    if verification.get("decision") == "reuse":
        return "guard_sql"
    return "generate_model_sql"


def _route_generated_sql_intent(state: AnalysisGraphState) -> str:
    verification = state.get("sql_intent_verification", {})
    if verification.get("decision") == "accept":
        return "guard_sql"
    if state.get("repair_attempts", 0) < 1 and state.get("selected_sql", "").strip():
        return "repair_model_sql"
    return "guard_sql"


def _route_execution_result(state: AnalysisGraphState) -> str:
    execution = state.get("execution")
    if not execution or execution.status not in {"error", "blocked"}:
        return "update_memory"
    if state.get("execution_repair_attempts", 0) >= 1:
        return "update_memory"
    if not state.get("selected_sql", "").strip():
        return "update_memory"
    return "repair_model_sql"


def _verify_memory_sql_node(state: AnalysisGraphState) -> AnalysisGraphState:
    started = perf_counter()
    reuse_plan = state["reuse_plan"]
    selected_sql = reuse_plan.selected_sql or ""
    verification = _verify_memory_sql(
        question=state["question"],
        retrieval_context=state["retrieval_context"],
        reuse_plan=reuse_plan,
        sql=selected_sql,
        question_intent=state.get("question_intent"),
    )
    if verification["decision"] == "reuse":
        return {
            "memory_verification": verification,
            "generated_sql": GeneratedSql(
                path="memory_reuse_verified",
                sql=selected_sql,
                warnings=verification["warnings"],
            ),
            "selected_sql": selected_sql,
            "node_timings": _add_node_timing(state, "memory_sql_verification", started),
        }

    rewrite_plan = reuse_plan.model_copy(
        update={
            "path_type": "rewrite_path",
            "reuse_type": "regenerate",
            "memory_hit": False,
            "selected_sql": selected_sql,
        }
    )
    return {
        "memory_verification": verification,
        "reuse_plan": rewrite_plan,
        "node_timings": _add_node_timing(state, "memory_sql_verification", started),
    }


def _verify_memory_sql(
    *,
    question: str,
    retrieval_context: RetrievalContext,
    reuse_plan: SqlReusePlan,
    sql: str,
    question_intent: dict[str, Any] | None = None,
) -> dict[str, Any]:
    warnings = _sql_intent_warnings(
        question=question,
        retrieval_context=retrieval_context,
        sql=sql,
        subject="候选 SQL",
        include_context_metrics=True,
        question_intent=question_intent,
    )
    if reuse_plan.path_type != "fast_path":
        warnings.append("候选 SQL 未达到 fast_path 置信阈值，仅作为模型改写参考。")

    decision = "reuse" if not warnings else "rewrite"
    return {
        "decision": decision,
        "confidence": reuse_plan.score,
        "warnings": warnings,
        "required": _sql_intent_required(
            question,
            retrieval_context,
            include_context_metrics=True,
            question_intent=question_intent,
        ),
        "observed": _sql_features(sql),
    }


def _generate_model_sql_node(state: AnalysisGraphState) -> AnalysisGraphState:
    started = perf_counter()
    question = state["question"]
    retrieval_context = state["retrieval_context"]
    reuse_plan = state["reuse_plan"]
    generated_sql = _select_generated_sql_compat(
        question=question,
        retrieval_context=retrieval_context,
        reuse_plan=reuse_plan,
        question_intent=state.get("question_intent"),
    )
    selected_sql = generated_sql.sql
    if reuse_plan.memory_hit:
        reuse_plan = reuse_plan.model_copy(update={"selected_sql": selected_sql})
    return {
        "generated_sql": generated_sql,
        "selected_sql": selected_sql,
        "reuse_plan": reuse_plan,
        "repair_attempts": 0,
        "execution_repair_attempts": 0,
        "node_timings": _add_node_timing(state, "sql_generation", started),
    }


def _validate_generated_sql_intent_node(state: AnalysisGraphState) -> AnalysisGraphState:
    started = perf_counter()
    generated_sql = state["generated_sql"]
    if generated_sql.path == "memory_reuse_verified":
        return {
            "sql_intent_verification": {"decision": "accept", "warnings": []},
            "node_timings": _add_node_timing(state, "sql_intent_validation", started),
        }

    verification = _verify_generated_sql_intent(
        question=state["question"],
        retrieval_context=state["retrieval_context"],
        sql=state.get("selected_sql", ""),
        question_intent=state.get("question_intent"),
    )
    inspector_issues = inspect_query_plan(
        state.get("selected_sql", ""),
        state.get("question_intent", {}).get("query_plan", {}),
    )
    if inspector_issues:
        verification["warnings"] = [*verification["warnings"], *(issue.message for issue in inspector_issues)]
        verification["inspector_issues"] = [issue.__dict__ for issue in inspector_issues]
        verification["decision"] = "reject"
    warnings = [*generated_sql.warnings]
    for warning in verification["warnings"]:
        if warning not in warnings:
            warnings.append(warning)

    updates: AnalysisGraphState = {
        "sql_intent_verification": verification,
        "generated_sql": generated_sql.model_copy(update={"warnings": warnings}),
        "node_timings": _add_node_timing(state, "sql_intent_validation", started),
    }
    cannot_repair = not state.get("selected_sql", "").strip() or state.get("repair_attempts", 0) >= 1
    if verification["decision"] == "reject" and cannot_repair:
        fallback_sql = _single_order_count_fallback(state.get("question_intent"))
        if fallback_sql:
            fallback_verification = _verify_generated_sql_intent(
                question=state["question"],
                retrieval_context=state["retrieval_context"],
                sql=fallback_sql,
                question_intent=state.get("question_intent"),
            )
            if fallback_verification["decision"] == "accept":
                fallback_warning = "模型生成与修复未满足 QuerySpec，已使用受控订单数 fallback。"
                updates["sql_intent_verification"] = fallback_verification
                updates["generated_sql"] = GeneratedSql(
                    path="query_spec_fallback",
                    sql=fallback_sql,
                    warnings=[*warnings, fallback_warning],
                )
                updates["selected_sql"] = fallback_sql
                return updates
        updates["generated_sql"] = generated_sql.model_copy(
            update={
                "path": "model_error",
                "sql": "",
                "warnings": warnings,
            }
        )
        updates["selected_sql"] = ""
    return updates


def _repair_model_sql_node(state: AnalysisGraphState) -> AnalysisGraphState:
    started = perf_counter()
    generated_sql = state["generated_sql"]
    verification = state.get("sql_intent_verification", {})
    execution = state.get("execution")
    guard = state.get("guard")
    previous_sql = (guard.final_sql if guard and guard.final_sql else state.get("selected_sql", ""))
    repair_context = {
        "previous_sql": previous_sql,
        "intent_errors": verification.get("warnings", []),
        "required": verification.get("required", {}),
        "observed": _json_safe(verification.get("observed", {})),
        "inspector_issues": verification.get("inspector_issues", []),
    }
    if execution and execution.status == "error":
        repair_context["execution_error"] = {
            "category": execution.error_category or "runtime",
            "message": execution.error_message or "",
            "user_summary": execution.user_error_message or "",
        }
    if execution and execution.status == "blocked":
        repair_context["guard_error"] = {
            "category": execution.error_category or "guard_blocked",
            "message": execution.error_message or "",
            "guard_errors": guard.errors if guard else [],
            "user_summary": execution.user_error_message or "",
        }
    repaired_sql = _select_generated_sql_compat(
        question=state["question"],
        retrieval_context=state["retrieval_context"],
        reuse_plan=state["reuse_plan"],
        repair_context=repair_context,
        adapter=state.get("_test_adapter"),
        question_intent=state.get("question_intent"),
    )
    warnings = [*generated_sql.warnings, *repaired_sql.warnings]
    return {
        "generated_sql": repaired_sql.model_copy(update={"warnings": warnings}),
        "selected_sql": repaired_sql.sql,
        "repair_attempts": state.get("repair_attempts", 0) + 1,
        "execution_repair_attempts": (
            state.get("execution_repair_attempts", 0) + 1
            if execution and execution.status in {"error", "blocked"}
            else state.get("execution_repair_attempts", 0)
        ),
        "node_timings": _add_node_timing(state, "sql_repair", started),
    }


def _guard_sql_node(state: AnalysisGraphState) -> AnalysisGraphState:
    started = perf_counter()
    selected_sql = state["selected_sql"]
    if not selected_sql.strip():
        generated_sql = state.get("generated_sql")
        errors = generated_sql.warnings if generated_sql else ["SQL 生成失败，未得到可执行 SQL。"]
        return {
            "guard": SqlGuardResult(
                allowed=False,
                errors=errors,
                warnings=state.get("memory_verification", {}).get("warnings", []),
            ),
            "node_timings": _add_node_timing(state, "sql_guard", started),
        }
    guard = guard_sql(selected_sql, max_rows=settings.sql_max_rows)
    return {"guard": guard, "node_timings": _add_node_timing(state, "sql_guard", started)}


def _execute_sql_node(state: AnalysisGraphState) -> AnalysisGraphState:
    started = perf_counter()
    guard = state["guard"]
    execution = execute_guarded_sql(guard)
    latency_ms = int((perf_counter() - state["started"]) * 1000)
    return {
        "execution": execution,
        "latency_ms": latency_ms,
        "node_timings": _add_node_timing(state, "sql_execution", started),
    }


def _update_memory_node(state: AnalysisGraphState) -> AnalysisGraphState:
    started = perf_counter()
    execution = state["execution"]
    guard = state["guard"]
    selected_sql = state["selected_sql"]
    updated_memory_id = None
    if execution.status == "success" and guard.allowed:
        query_spec = _query_spec_from_intent(state.get("question_intent"))
        updated_memory = upsert_successful_sql_memory(
            question=state["question"],
            sql_template=guard.final_sql or selected_sql,
            final_sql=guard.final_sql or selected_sql,
            parameters={
                "generation_path": state["generated_sql"].path,
                "model_provider": state["generated_sql"].model_provider,
                "model_name": state["generated_sql"].model_name,
            },
            tables=sorted(_extract_sql_tables(guard.final_sql or selected_sql)),
            metrics=query_spec.metrics if query_spec else state["metric_names"],
            dimensions=query_spec.dimensions if query_spec else [],
            result_columns=execution.columns,
            row_count=execution.row_count,
            latency_ms=execution.latency_ms,
        )
        updated_memory_id = updated_memory.id
    return {
        "updated_memory_id": updated_memory_id,
        "node_timings": _add_node_timing(state, "memory_update", started),
    }


def _present_result_node(state: AnalysisGraphState) -> AnalysisGraphState:
    started = perf_counter()
    guard = state["guard"]
    execution = state["execution"]
    presented_execution = (
        execution.model_copy(update={"error_message": execution.user_error_message})
        if execution.status == "error" and execution.user_error_message
        else execution
    )
    selected_sql = state["selected_sql"]
    response = present_sales_trend_result(
        question=state["question"],
        sql=guard.final_sql or selected_sql,
        execution=presented_execution,
        guard_warnings=guard.warnings,
        latency_ms=state["latency_ms"],
        retrieval_context=state["retrieval_context"],
        reuse_plan=state["reuse_plan"],
    )
    return {
        "response": response,
        "node_timings": _add_node_timing(state, "present_result", started),
    }


def _log_run_node(state: AnalysisGraphState) -> AnalysisGraphState:
    guard = state["guard"]
    execution = state["execution"]
    retrieval_context = state["retrieval_context"]
    reuse_plan = state["reuse_plan"]
    generated_sql = state["generated_sql"]
    selected_sql = state["selected_sql"]
    _log_analysis_run(
        app_user_id=state.get("app_user_id"),
        question=state.get("original_question", state["question"]),
        rewritten_question=state["question"],
        final_sql=guard.final_sql or selected_sql,
        guard_status="allowed" if guard.allowed else "blocked",
        execution_status=execution.status,
        row_count=execution.row_count,
        latency_ms=state["latency_ms"],
        memory_hit=reuse_plan.memory_hit,
        memory_id=reuse_plan.selected_memory_id,
        memory_candidate_count=len(state["memory_candidates"]),
        reuse_plan=reuse_plan,
        generation_path=generated_sql.path,
        generated_sql_text=selected_sql,
        updated_memory_id=state["updated_memory_id"],
        error_message=execution.error_message or "; ".join(guard.errors) or None,
        metric_count=len(retrieval_context.metrics),
        schema_column_count=len(retrieval_context.schema_columns),
        relationship_count=len(retrieval_context.table_relationships),
        context_tables=retrieval_context.tables,
        context_fields=retrieval_context.fields,
        rerank_diagnostics=retrieval_context.rerank_diagnostics,
        generation_warnings=generated_sql.warnings,
        intent_verification=state.get("sql_intent_verification", {}),
        repair_attempts=state.get("repair_attempts", 0),
        guard_warnings=guard.warnings,
        guard_errors=guard.errors,
        node_timings=state.get("node_timings", {}),
    )
    return {}


def _log_analysis_run(
    *,
    app_user_id: UUID | None,
    question: str,
    rewritten_question: str | None,
    final_sql: str,
    guard_status: str,
    execution_status: str,
    row_count: int,
    latency_ms: int,
    memory_hit: bool,
    memory_id,
    memory_candidate_count: int,
    reuse_plan: SqlReusePlan,
    updated_memory_id,
    generation_path: str,
    generated_sql_text: str,
    error_message: str | None,
    metric_count: int,
    schema_column_count: int,
    relationship_count: int,
    context_tables: list[str],
    context_fields: list[str],
    rerank_diagnostics: dict[str, Any],
    generation_warnings: list[str],
    intent_verification: dict[str, Any],
    repair_attempts: int,
    guard_warnings: list[str],
    guard_errors: list[str],
    node_timings: dict[str, int],
) -> None:
    logger = QueryRunLogger()
    run = logger.log_run(
        app_user_id=app_user_id,
        user_question=question,
        rewritten_question=rewritten_question,
        generated_sql=generated_sql_text,
        final_sql=final_sql,
        guard_status=guard_status,
        execution_status=execution_status,
        row_count=row_count,
        latency_ms=latency_ms,
        memory_hit=memory_hit,
        memory_id=memory_id,
        error_message=error_message,
    )
    logger.log_tool_call(
        query_run_id=run.id,
        tool_name="sql_memory_tools.retrieve_sql_memory",
        input_payload={"question": question},
        output_payload={"candidate_count": memory_candidate_count},
        status="success",
        latency_ms=node_timings.get("memory_retrieval_and_plan", 0),
    )
    logger.log_tool_call(
        query_run_id=run.id,
        tool_name="sql_memory_tools.plan_sql_reuse",
        input_payload={"candidate_count": memory_candidate_count},
        output_payload={
            "path_type": reuse_plan.path_type,
            "reuse_type": reuse_plan.reuse_type,
            "memory_hit": reuse_plan.memory_hit,
            "score": reuse_plan.score,
        },
        status="success",
        latency_ms=node_timings.get("memory_retrieval_and_plan", 0),
    )
    logger.log_tool_call(
        query_run_id=run.id,
        tool_name="context_builder.build_retrieval_context",
        input_payload={"question": question},
        output_payload={
            "metric_count": metric_count,
            "schema_column_count": schema_column_count,
            "relationship_count": relationship_count,
            "tables": context_tables,
            "fields_sample": context_fields[:20],
            "rerank_diagnostics": rerank_diagnostics,
        },
        status="success",
        latency_ms=node_timings.get("context_retrieval", 0),
    )
    logger.log_tool_call(
        query_run_id=run.id,
        tool_name="analysis_graph.select_generated_sql",
        input_payload={"path_type": reuse_plan.path_type},
        output_payload={
            "generation_path": generation_path,
            "has_sql": bool(generated_sql_text),
            "warning_count": len(generation_warnings),
            "warnings": generation_warnings[:5],
            "intent_verification": {
                "decision": intent_verification.get("decision"),
                "warning_count": len(intent_verification.get("warnings", [])),
                "warnings": intent_verification.get("warnings", [])[:5],
                "repair_attempts": repair_attempts,
            },
            "context_table_coverage": _context_table_coverage(
                generated_sql_text,
                context_tables,
            ),
        },
        status="success",
        latency_ms=node_timings.get("sql_generation", 0),
    )
    logger.log_tool_call(
        query_run_id=run.id,
        tool_name="sql_validation_tools.guard_sql",
        input_payload={"max_rows": 30},
        output_payload={
            "guard_status": guard_status,
            "warning_count": len(guard_warnings),
            "warnings": guard_warnings[:5],
            "error_count": len(guard_errors),
            "errors": guard_errors[:5],
        },
        status="success" if guard_status == "allowed" else "blocked",
        latency_ms=node_timings.get("sql_guard", 0),
    )
    logger.log_tool_call(
        query_run_id=run.id,
        tool_name="sql_execution_tools.execute_guarded_sql",
        input_payload={"guard_status": guard_status},
        output_payload={"execution_status": execution_status, "row_count": row_count},
        status=execution_status,
        latency_ms=node_timings.get("sql_execution", 0),
    )
    logger.log_tool_call(
        query_run_id=run.id,
        tool_name="analysis_presenter.present_sales_trend_result",
        input_payload={"row_count": row_count},
        output_payload={"response_status": "success" if not error_message else "error"},
        status="success" if not error_message else "error",
        latency_ms=node_timings.get("present_result", 0),
    )
    logger.log_tool_call(
        query_run_id=run.id,
        tool_name="sql_memory_tools.upsert_successful_sql_memory",
        input_payload={"memory_hit": memory_hit},
        output_payload={"updated_memory_id": str(updated_memory_id) if updated_memory_id else None},
        status="success" if updated_memory_id else "skipped",
        latency_ms=node_timings.get("memory_update", 0),
    )
    logger.log_tool_call(
        query_run_id=run.id,
        tool_name="analysis_graph.pipeline_timings",
        input_payload={"question": question},
        output_payload={
            "node_timings_ms": node_timings,
            "total_latency_ms": latency_ms,
            "slowest_node": _slowest_node(node_timings),
        },
        status="success",
        latency_ms=latency_ms,
    )


def _select_generated_sql(
    *,
    question: str,
    retrieval_context: RetrievalContext,
    reuse_plan: SqlReusePlan,
    adapter: ModelAdapter | None = None,
    model_enabled: bool | None = None,
    repair_context: dict[str, Any] | None = None,
    question_intent: dict[str, Any] | None = None,
) -> GeneratedSql:
    enabled = settings.model_sql_generator_enabled if model_enabled is None else model_enabled
    if not enabled:
        return GeneratedSql(
            path="model_error",
            warnings=["Model SQL generation is disabled and the fixed template main path has been removed."],
        )

    model_result = generate_sql_with_model(
        question=question,
        retrieval_context=retrieval_context,
        reuse_plan=reuse_plan,
        adapter=adapter,
        repair_context=repair_context,
        question_intent=question_intent,
    )
    warnings = [*model_result.warnings]
    if model_result.sql:
        coverage = _context_table_coverage(model_result.sql, retrieval_context.tables)
        if not coverage["covered"]:
            warnings.append(_context_table_coverage_warning(coverage["missing_tables"]))
    else:
        warnings.append(
            "Model did not return executable SQL; fixed template generation is no longer used on the main path."
        )

    return model_result.model_copy(update={"warnings": warnings})


def _single_order_count_fallback(question_intent: dict[str, Any] | None) -> str:
    """只覆盖无维度的已支付订单数，避免小模型在明确口径上反复生成错误 SQL。"""
    query_spec = _query_spec_from_intent(question_intent)
    if query_spec is None or query_spec.metrics != ["order_count"]:
        return ""
    if query_spec.dimensions or query_spec.top_n or query_spec.requires_order_by:
        return ""

    filters = [
        "EXISTS (",
        "  SELECT 1",
        "  FROM payments pay",
        "  WHERE pay.order_id = o.id",
        "    AND pay.status = 'paid'",
        ")",
    ]
    if query_spec.time_start and query_spec.time_end:
        filters.extend(
            [
                f"AND o.created_at >= DATE '{query_spec.time_start}'",
                f"AND o.created_at < DATE '{query_spec.time_end}'",
            ]
        )
    return "\n".join(
        [
            "SELECT COUNT(DISTINCT o.id) AS order_count",
            "FROM orders o",
            "WHERE " + filters[0],
            *filters[1:],
            "LIMIT 1",
        ]
    )


def _select_generated_sql_compat(**kwargs) -> GeneratedSql:
    try:
        return _select_generated_sql(**kwargs)
    except TypeError as exc:
        if "question_intent" not in str(exc):
            raise
        fallback_kwargs = dict(kwargs)
        question_intent = fallback_kwargs.pop("question_intent", None)
        if isinstance(question_intent, dict) and question_intent.get("original_question"):
            fallback_kwargs["question"] = str(question_intent["original_question"])
        return _select_generated_sql(**fallback_kwargs)


def _verify_generated_sql_intent(
    *,
    question: str,
    retrieval_context: RetrievalContext,
    sql: str,
    question_intent: dict[str, Any] | None = None,
) -> dict[str, Any]:
    warnings = _sql_intent_warnings(
        question=question,
        retrieval_context=retrieval_context,
        sql=sql,
        subject="模型 SQL",
        question_intent=question_intent,
    )
    decision = "accept" if not warnings else "reject"
    return {
        "decision": decision,
        "warnings": warnings,
        "required": _sql_intent_required(
            question,
            retrieval_context,
            include_context_metrics=False,
            question_intent=question_intent,
        ),
        "observed": _sql_features(sql),
    }


def _sql_intent_warnings(
    *,
    question: str,
    retrieval_context: RetrievalContext,
    sql: str,
    subject: str,
    include_context_metrics: bool = False,
    question_intent: dict[str, Any] | None = None,
) -> list[str]:
    warnings: list[str] = []
    required = _sql_intent_required(
        question,
        retrieval_context,
        include_context_metrics=include_context_metrics,
        question_intent=question_intent,
    )
    observed = _sql_features(sql)
    coverage = _context_table_coverage(sql, retrieval_context.tables)

    if not sql.strip():
        warnings.append(f"{subject} 为空，无法执行。")
    missing_tables = _allowed_context_table_exceptions(
        question=question,
        observed_text=observed["text"],
        missing_tables=coverage["missing_tables"],
    )
    if missing_tables:
        warnings.append(_context_table_coverage_warning(missing_tables))
    for table in required["required_tables"]:
        if table not in observed["tables"]:
            warnings.append(f"{subject} 缺少当前问题需要的数据表：{table}")
    for token in required["required_metric_tokens"]:
        if not _token_present(token, observed["text"]):
            warnings.append(f"{subject} 缺少当前问题需要的指标口径：{token}")
    for token in required["required_dimension_tokens"]:
        if not _token_present(token, observed["text"]):
            warnings.append(f"{subject} 缺少当前问题需要的维度：{token}")
    if required["granularity"] and required["granularity"] != observed["granularity"]:
        warnings.append(
            f"{subject} 时间粒度不匹配：需要 {required['granularity']}，实际 {observed['granularity'] or 'unknown'}"
        )
    if required.get("time_start") and not _sql_has_time_bounds(
        sql,
        required["time_start"],
        required["time_end"],
    ):
        warnings.append(
            f"{subject} 未满足明确时间范围：必须使用 {required['time_filter']}。"
        )
    if required["top_n"] and not observed["has_order_by"]:
        warnings.append(f"当前问题需要 Top/排行语义，但{subject}缺少 ORDER BY。")
    if required["limit"] and observed["limit"] and observed["limit"] > required["limit"]:
        warnings.append(f"{subject} LIMIT {observed['limit']} 大于当前问题要求的 {required['limit']}。")
    if _uses_orders_status_paid(sql):
        warnings.append(
            f"{subject} 使用了错误支付口径：orders.status 没有 paid，请关联 payments 并使用 payments.status = 'paid'。"
        )
    if _duplicates_order_amount_through_payments_join(sql):
        warnings.append(
            f"{subject} 可能在 JOIN payments 后直接汇总 orders.total_amount，"
            "一单多支付会导致订单金额重复累计；请先按 orders.id 去重或先按 payments.order_id 聚合。"
        )
    return warnings


def _sql_intent_required(
    question: str,
    retrieval_context: RetrievalContext,
    *,
    include_context_metrics: bool = False,
    question_intent: dict[str, Any] | None = None,
) -> dict[str, Any]:
    query_spec = _query_spec_from_intent(question_intent)
    if query_spec:
        required = {
            "required_tables": query_spec.required_tables,
            "required_metric_tokens": query_spec.required_metric_tokens,
            "required_dimension_tokens": query_spec.required_dimension_tokens,
            "granularity": query_spec.granularity,
            "top_n": query_spec.requires_order_by,
            "limit": query_spec.top_n,
            "time_start": query_spec.time_start,
            "time_end": query_spec.time_end,
            "time_filter": query_spec.time_filter,
        }
    else:
        required = _question_sql_requirements(question)
    if include_context_metrics:
        required["required_metric_tokens"] = sorted(
            set(required["required_metric_tokens"])
            | set(_context_metric_tokens(retrieval_context))
        )
    return required


def _query_spec_from_intent(question_intent: dict[str, Any] | None) -> QuerySpec | None:
    if not isinstance(question_intent, dict):
        return None
    payload = question_intent.get("query_spec")
    if not isinstance(payload, dict):
        return None
    try:
        return QuerySpec.model_validate(payload)
    except ValueError:
        return None


def _json_safe(value: Any) -> Any:
    if isinstance(value, set):
        return sorted(value)
    if isinstance(value, dict):
        return {key: _json_safe(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_json_safe(item) for item in value]
    return value


def _token_present(token: str, lowered_sql: str) -> bool:
    aliases = {
        "repeat": ["repeat", "repeat_rate", "paid_order_count"],
        "product": ["product", "product_id", "product_label"],
        "category": ["category", "category_label"],
        "payment_method": ["payment_method", "payment_type", "payment_method_label"],
        "date": ["date", "order_date", "created_at", "date_trunc('day'"],
        "month": ["month", "order_month", "date_trunc('month'"],
        "total_amount": ["total_amount", "sales_amount", "daily_sales", "gmv"],
        "new_user_count": ["new_user_count", "new_users", "count(distinct u.id"],
        "ordering_user_count": ["ordering_user_count", "order_user_count", "count(distinct o.user_id"],
        "purchase_count": ["purchase_count", "order_count", "count(distinct o.id"],
        "conversion_rate": ["conversion_rate", "conversion", "convert_rate"],
        "coupon_redemption_rate": ["coupon_redemption_rate", "redemption_rate", "redeem_rate"],
        "source": ["source", "traffic_source", "channel"],
        "user": ["user", "user_id", "user_label"],
        "coupon": ["coupon", "coupon_id", "coupon_code"],
    }
    return any(alias in lowered_sql for alias in aliases.get(token, [token]))


def _allowed_context_table_exceptions(
    *,
    question: str,
    observed_text: str,
    missing_tables: list[str],
) -> list[str]:
    filtered = set(missing_tables)
    if (
        "users" in filtered
        and any(token in question for token in ["复购率", "复购", "回购"])
        and "user_id" in observed_text
        and _token_present("repeat", observed_text)
    ):
        filtered.remove("users")
    return sorted(filtered)


def _context_table_coverage(sql: str, context_tables: list[str]) -> dict:
    required_tables = _required_context_tables(context_tables)
    sql_tables = _extract_sql_tables(sql)
    missing_tables = sorted(required_tables - sql_tables)
    return {
        "required_tables": sorted(required_tables),
        "sql_tables": sorted(sql_tables),
        "missing_tables": missing_tables,
        "covered": not missing_tables,
    }


def _required_context_tables(context_tables: list[str]) -> set[str]:
    return {
        table
        for table in context_tables
        if table and table not in BASE_TRANSACTION_TABLES
    }


def _extract_sql_tables(sql: str) -> set[str]:
    if not sql.strip():
        return set()
    try:
        expression = parse_one(sql, dialect="postgres")
    except ParseError:
        return set()
    return {table.name for table in expression.find_all(exp.Table) if table.name}


def _context_table_coverage_warning(missing_tables: list[str]) -> str:
    return "SQL 未覆盖已召回的关键上下文表：" + ", ".join(missing_tables)


def _question_sql_requirements(question: str) -> dict[str, Any]:
    return {
        "required_tables": _required_tables_for_question(question),
        "required_metric_tokens": _required_metric_tokens(question),
        "required_dimension_tokens": _required_dimension_tokens(question),
        "granularity": _required_granularity(question),
        "top_n": _requires_top_n(question),
        "limit": _required_limit(question),
        "time_start": "",
        "time_end": "",
        "time_filter": "",
    }


def _context_metric_tokens(retrieval_context: RetrievalContext) -> list[str]:
    tokens: list[str] = []
    for metric in retrieval_context.metrics:
        metric_text = " ".join(
            [
                metric.metric_name,
                metric.display_name,
                metric.description,
                metric.formula,
            ]
        ).lower()
        if "repeat" in metric_text or "复购" in metric_text or "回购" in metric_text:
            tokens.append("repeat")
        if "gross_margin" in metric_text or "毛利" in metric_text:
            tokens.append("gross_margin")
        if "success_rate" in metric_text or "支付成功" in metric_text:
            tokens.append("success_rate")
        if "failure_rate" in metric_text or "支付失败" in metric_text:
            tokens.append("failure_rate")
        if "refund_rate" in metric_text or "退款率" in metric_text:
            tokens.append("refund_rate")
        if "avg_order_value" in metric_text or "客单价" in metric_text:
            tokens.append("avg_order_value")
        if "order_count" in metric_text or "订单数" in metric_text:
            tokens.append("order_count")
        if "sales_amount" in metric_text or "total_amount" in metric_text or "销售额" in metric_text:
            tokens.append("total_amount")
    return sorted(set(tokens))


def _sql_features(sql: str) -> dict[str, Any]:
    lowered = sql.lower()
    return {
        "text": lowered,
        "tables": _extract_sql_tables(sql),
        "granularity": _sql_granularity(lowered),
        "has_order_by": "order by" in lowered,
        "limit": _sql_limit(sql),
    }


def _uses_orders_status_paid(sql: str) -> bool:
    if not sql.strip():
        return False
    try:
        expression = parse_one(sql, dialect="postgres")
    except ParseError:
        return False

    alias_to_table = {
        table.alias_or_name: table.name
        for table in expression.find_all(exp.Table)
        if table.name
    }
    alias_to_table.update({table.name: table.name for table in expression.find_all(exp.Table) if table.name})

    for equality in expression.find_all(exp.EQ):
        left = equality.left
        right = equality.right
        if _is_paid_literal(right) and _is_orders_status_column(left, alias_to_table):
            return True
        if _is_paid_literal(left) and _is_orders_status_column(right, alias_to_table):
            return True
    return False


def _duplicates_order_amount_through_payments_join(sql: str) -> bool:
    if not sql.strip():
        return False
    try:
        expression = parse_one(sql, dialect="postgres")
    except ParseError:
        return False

    for select in expression.find_all(exp.Select):
        joins = select.args.get("joins") or []
        joined_tables = {
            join.this.name
            for join in joins
            if isinstance(join.this, exp.Table) and join.this.name
        }
        if "payments" not in joined_tables:
            continue

        alias_to_table = {
            table.alias_or_name: table.name
            for table in select.find_all(exp.Table)
            if table.name and table.find_ancestor(exp.Select) is select
        }
        alias_to_table.update({table: table for table in alias_to_table.values()})

        for aggregate in select.find_all(exp.Sum):
            if aggregate.find_ancestor(exp.Select) is not select or _sum_uses_distinct(aggregate):
                continue
            for column in aggregate.find_all(exp.Column):
                if column.name != "total_amount":
                    continue
                table_name = alias_to_table.get(column.table or "")
                if table_name == "orders":
                    return True
    return False


def _sum_uses_distinct(aggregate: exp.Sum) -> bool:
    return isinstance(aggregate.this, exp.Distinct) or bool(aggregate.args.get("distinct"))


def _is_paid_literal(expression: exp.Expression | None) -> bool:
    return isinstance(expression, exp.Literal) and str(expression.this).lower() == "paid"


def _is_orders_status_column(
    expression: exp.Expression | None,
    alias_to_table: dict[str, str],
) -> bool:
    if not isinstance(expression, exp.Column):
        return False
    table_name = alias_to_table.get(expression.table or "")
    if expression.name != "status":
        return False
    if table_name == "orders":
        return True
    return not expression.table and set(alias_to_table.values()) == {"orders"}


def _required_tables_for_question(question: str) -> list[str]:
    required: list[str] = []
    if any(token in question for token in ["新增用户", "新用户", "下单用户", "购买用户", "购买次数最多", "用户是谁"]):
        required.append("users")
    if any(token in question for token in ["访问", "加购", "流量来源", "转化率"]):
        required.append("traffic_events")
    if any(token in question for token in ["优惠券", "核销"]):
        required.append("coupon_usages")
    if any(token in question for token in ["哪些优惠券", "优惠券核销"]):
        required.append("coupons")
    return required


def _required_metric_tokens(question: str) -> list[str]:
    checks: list[tuple[list[str], list[str]]] = [
        (["复购率", "复购", "回购"], ["repeat"]),
        (["客单价", "平均订单", "平均金额"], ["avg_order_value"]),
        (["毛利率", "毛利", "利润率"], ["gross_margin"]),
        (["支付失败率", "失败率"], ["failure_rate"]),
        (["支付成功率", "成功率"], ["success_rate"]),
        (["退款率"], ["refund_rate"]),
        (["订单数", "订单量"], ["order_count"]),
        (["销售额", "销售金额", "GMV", "成交额"], ["total_amount"]),
    ]
    return [token for keywords, tokens in checks if any(keyword in question for keyword in keywords) for token in tokens]


def _required_dimension_tokens(question: str) -> list[str]:
    checks: list[tuple[list[str], list[str]]] = [
        (["每月", "按月", "月度", "分月"], ["month"]),
        (["每天", "按天", "日趋势"], ["date"]),
        (["商品"], ["product"]),
        (["品类", "类目"], ["category"]),
        (["城市", "地区", "地域"], ["city"]),
        (["支付方式"], ["payment_method"]),
        (["流量来源"], ["source"]),
    ]
    return [token for keywords, tokens in checks if any(keyword in question for keyword in keywords) for token in tokens]


def _required_granularity(question: str) -> str | None:
    if any(token in question for token in ["每月", "按月", "月度", "分月"]):
        return "month"
    if any(token in question for token in ["每天", "按天", "日趋势"]):
        return "day"
    return None


def _requires_top_n(question: str) -> bool:
    ranking_tokens = ["最高", "最低", "排行", "排名"]
    return any(token in question for token in ranking_tokens) or bool(
        re.search(r"前\s*\d+", question)
    )


def _required_limit(question: str) -> int | None:
    match = re.search(r"前\s*(\d+)\s*个?", question)
    if match:
        return int(match.group(1))
    return None


def _sql_has_time_bounds(sql: str, start: str, end: str) -> bool:
    """Require both endpoints; the generator receives the exact half-open predicate."""
    if not sql.strip() or not start or not end:
        return False
    lowered = sql.lower()
    date_literal = r"(?:date\s+)?['\"]{}['\"]"
    has_start = re.search(r">=\s*" + date_literal.format(re.escape(start)), lowered)
    has_end = re.search(r"<\s*" + date_literal.format(re.escape(end)), lowered)
    return bool(has_start and has_end)


def _sql_granularity(lowered_sql: str) -> str | None:
    if "date_trunc('month'" in lowered_sql or 'date_trunc("month"' in lowered_sql:
        return "month"
    if "date_trunc('day'" in lowered_sql or 'date_trunc("day"' in lowered_sql or "date(" in lowered_sql:
        return "day"
    return None


def _sql_limit(sql: str) -> int | None:
    try:
        expression = parse_one(sql, dialect="postgres")
    except ParseError:
        return None
    limit = expression.args.get("limit")
    if not limit:
        return None
    expression_value = limit.expression
    if expression_value is None:
        return None
    try:
        return int(expression_value.name)
    except (TypeError, ValueError):
        return None
