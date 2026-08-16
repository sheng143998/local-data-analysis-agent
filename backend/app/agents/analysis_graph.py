from functools import lru_cache
import re
from time import perf_counter
from typing import Any, TypedDict
from uuid import UUID, uuid4

from langgraph.graph import END, StateGraph
from sqlglot import exp, parse_one
from sqlglot.errors import ParseError

from backend.app.core.background import submit_bookkeeping
from backend.app.core.config import settings
from backend.app.core.model_adapter import ModelAdapter
from backend.app.services.cache_key_builder import build_query_cache_key
from backend.app.services.cache_service import get_cache_service
from backend.app.db.repositories.memory_repository import SqlMemoryRepository
from backend.app.schemas.analysis import AnalyzeResponse
from backend.app.schemas.retrieval import RetrievalContext
from backend.app.schemas.sql_generation import GeneratedSql
from backend.app.schemas.memories import SqlReusePlan
from backend.app.schemas.query_spec import QuerySpec
from backend.app.schemas.sql_execution import SqlExecutionResult, SqlExplainResult
from backend.app.schemas.sql_validation import SqlGuardResult
from backend.app.tools.analysis_presenter import present_clarification_response, present_sales_trend_result
from backend.app.tools.context_builder import build_retrieval_context
from backend.app.tools.model_sql_generator import generate_sql_with_model
from backend.app.tools.question_intent_parser import ParsedQuestionIntent, parse_question_intent
from backend.app.tools.run_logger import QueryRunLogger
from backend.app.tools.sql_memory_tools import (
    build_sql_memory_context_fingerprints,
    plan_sql_reuse,
    retrieve_sql_memory,
    upsert_successful_sql_memory,
)
from backend.app.tools.sql_execution_tools import execute_guarded_sql, explain_guarded_sql
from backend.app.tools.sql_validation_tools import guard_sql
from backend.app.tools.vector_retrieval import embed_question
from backend.app.tools.sql_inspector import inspect_query_plan
from backend.app.tools.result_contract_builder import build_result_contract

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
    run_id: UUID
    app_user_id: UUID | None
    original_question: str
    question_intent: dict[str, Any]
    node_timings: dict[str, int]
    started: float
    question_vector: list[float]
    precomputed_retrieval: Any
    cancel_event: Any
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
    sql_candidates: list[dict[str, Any]]
    guard: SqlGuardResult
    explain: SqlExplainResult
    execution: SqlExecutionResult
    latency_ms: int
    cache_key: str | None
    cache_hit: bool
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
    graph.add_node("explain_sql", _explain_sql_node)
    graph.add_node("execute_sql", _execute_sql_node)
    graph.add_node("present_result", _present_result_node)
    graph.add_node("bookkeeping", _bookkeeping_node)

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
    graph.add_edge("guard_sql", "explain_sql")
    # 记忆写回与日志（bookkeeping）移到 present_result 之后：
    # 响应先就绪，约 4.6s 的簿记工作不再占用用户可感知延迟（计划 1c）。
    graph.add_conditional_edges(
        "explain_sql",
        _route_explain_result,
        {"execute_sql": "execute_sql", "repair_model_sql": "repair_model_sql", "update_memory": "present_result"},
    )
    graph.add_conditional_edges(
        "execute_sql",
        _route_execution_result,
        {"repair_model_sql": "repair_model_sql", "update_memory": "present_result"},
    )
    graph.add_edge("present_result", "bookkeeping")
    graph.add_edge("bookkeeping", END)
    return graph.compile()


def run_analysis_graph(
    question: str,
    app_user_id: UUID | None = None,
    parsed_intent: ParsedQuestionIntent | None = None,
    precomputed_retrieval: Any = None,
    cancel_event: Any = None,
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
            "run_id": uuid4(),
            "app_user_id": app_user_id,
            "original_question": question,
            "question_intent": intent.model_dump(),
            "node_timings": {"intent_parse": latency_ms},
            "started": started,
            "precomputed_retrieval": precomputed_retrieval,
            "cancel_event": cancel_event,
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


def _raise_if_cancelled(state: AnalysisGraphState) -> None:
    """用户断开/取消后立即停止后续昂贵节点（计划 2d）。"""
    cancel_event = state.get("cancel_event")
    if cancel_event is not None and cancel_event.is_set():
        from backend.app.services.agent_service import AnalysisCancelledError

        raise AnalysisCancelledError("分析已被取消")


def _retrieve_context_node(state: AnalysisGraphState) -> AnalysisGraphState:
    started = perf_counter()
    _raise_if_cancelled(state)
    question = state["question"]
    precomputed = state.get("precomputed_retrieval")
    # 问题只 embed 一次：同一向量供指标召回、schema 召回、SQL Memory 召回与记忆写入复用；
    # 意图解析阶段已并行预取时（计划 2b）直接复用其产物，不再重复检索。
    if precomputed is not None and getattr(precomputed, "question_vector", None) is not None:
        question_vector = list(precomputed.question_vector)
    else:
        question_vector = embed_question(question)
    retrieval_context = build_retrieval_context(
        question,
        semantic_contracts=state.get("question_intent", {}).get("resolved_contracts", []),
        query_plan=state.get("question_intent", {}).get("query_plan", {}),
        question_vector=question_vector,
        precomputed_metrics=getattr(precomputed, "metrics", None),
        precomputed_schema=getattr(precomputed, "schema_columns", None),
    )
    metric_names = [metric.metric_name for metric in retrieval_context.metrics]
    return {
        "question_vector": question_vector,
        "retrieval_context": retrieval_context,
        "metric_names": metric_names,
        "node_timings": _add_node_timing(state, "context_retrieval", started),
    }


def _plan_memory_reuse_node(state: AnalysisGraphState) -> AnalysisGraphState:
    started = perf_counter()
    _raise_if_cancelled(state)
    question = state["question"]
    retrieval_context = state["retrieval_context"]
    metric_names = state["metric_names"]
    query_spec = _query_spec_from_intent(state.get("question_intent"))
    context_fingerprints = build_sql_memory_context_fingerprints(
        retrieval_context,
        state.get("question_intent", {}).get("resolved_contracts", []),
    )
    memory_candidates = retrieve_sql_memory(
        question,
        metrics=query_spec.metrics if query_spec else metric_names,
        tables=sorted(set(retrieval_context.tables) | set(query_spec.required_tables if query_spec else [])),
        required_tables=query_spec.required_tables if query_spec else None,
        context_fingerprints=context_fingerprints,
        question_vector=state.get("question_vector"),
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
    # 业务语义诊断只驱动一次修复；最终是否可执行由 Guard、EXPLAIN 和只读 Executor 决定。
    if state.get("repair_attempts", 0) < 1:
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


def _route_explain_result(state: AnalysisGraphState) -> str:
    """预检失败只允许有限修复，绝不直接进入主查询。"""
    explain = state.get("explain")
    if explain and explain.status == "success":
        return "execute_sql"
    if state.get("execution_repair_attempts", 0) < 1 and state.get("selected_sql", "").strip():
        return "repair_model_sql"
    return "update_memory"


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
        # SQL Memory 仅按已确认的 QuerySpec 复用，召回指标只是生成参考，不能阻断已审核 SQL。
        include_context_metrics=False,
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
            include_context_metrics=False,
            question_intent=question_intent,
        ),
        "observed": _sql_features(sql),
    }


def _verified_few_shot_examples(state: AnalysisGraphState) -> list[dict[str, str]]:
    """取 top-2 已验证记忆作为生成示例（计划 1d）。

    近邻 few-shot 是 text-to-SQL 的经典提准手段；只用 verified 记忆，
    避免把未审核 SQL 的错误模式当范例传播。
    """
    candidates = state.get("memory_candidates") or []
    examples: list[dict[str, str]] = []
    for candidate in candidates:
        memory = getattr(candidate, "memory", None)
        if memory is None or memory.trust_status != "verified":
            continue
        sql_lines = memory.final_sql.strip().splitlines()
        examples.append(
            {
                "question": memory.canonical_question,
                "sql": "\n".join(sql_lines[:40]),
            }
        )
        if len(examples) >= 2:
            break
    return examples


def _generate_model_sql_node(state: AnalysisGraphState) -> AnalysisGraphState:
    started = perf_counter()
    _raise_if_cancelled(state)
    question = state["question"]
    retrieval_context = state["retrieval_context"]
    reuse_plan = state["reuse_plan"]
    generated_sql = _select_generated_sql_compat(
        question=question,
        retrieval_context=retrieval_context,
        reuse_plan=reuse_plan,
        question_intent=state.get("question_intent"),
        few_shot_examples=_verified_few_shot_examples(state),
    )
    selected_sql = generated_sql.sql
    if reuse_plan.memory_hit:
        reuse_plan = reuse_plan.model_copy(update={"selected_sql": selected_sql})
    return {
        "generated_sql": generated_sql,
        "selected_sql": selected_sql,
        "sql_candidates": [_sql_candidate("generation", generated_sql)],
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
    # Inspector 和意图检查描述目标口径，不把等价 SQL 写法升级为最终阻断条件。
    # 空 SQL 仍会在 Guard 被拒绝；有 SQL 时给一次 Repair，随后交给安全执行链路裁决。
    has_sql = bool(state.get("selected_sql", "").strip())
    verification["decision"] = (
        "reject" if not has_sql else "accept" if not verification["warnings"] else "repair"
    )
    warnings = [*generated_sql.warnings]
    for warning in verification["warnings"]:
        if warning not in warnings:
            warnings.append(warning)

    updates: AnalysisGraphState = {
        "sql_intent_verification": verification,
        "generated_sql": generated_sql.model_copy(update={"warnings": warnings}),
        "selected_sql": state.get("selected_sql", ""),
        "node_timings": _add_node_timing(state, "sql_intent_validation", started),
    }
    # 空响应不是 SQL 的等价写法；一次 Repair 仍为空时保持安全失败，不能进入 Guard/Executor。
    if not has_sql and state.get("repair_attempts", 0) >= 1:
        updates["generated_sql"] = generated_sql.model_copy(
            update={"path": "model_error", "sql": "", "warnings": warnings}
        )
        updates["selected_sql"] = ""
    return updates


def _repair_model_sql_node(state: AnalysisGraphState) -> AnalysisGraphState:
    started = perf_counter()
    _raise_if_cancelled(state)
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
        few_shot_examples=_verified_few_shot_examples(state),
    )
    warnings = [*generated_sql.warnings, *repaired_sql.warnings]
    return {
        "generated_sql": repaired_sql.model_copy(update={"warnings": warnings}),
        "selected_sql": repaired_sql.sql,
        "sql_candidates": [*state.get("sql_candidates", []), _sql_candidate("repair", repaired_sql)],
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
    _raise_if_cancelled(state)
    guard = state["guard"]

    if state.get("cache_hit") and state.get("execution") is not None:
        return {
            "execution": state["execution"],
            "latency_ms": state.get("latency_ms", int((perf_counter() - state["started"]) * 1000)),
            "node_timings": _add_node_timing(state, "sql_execution", started),
        }

    execution = execute_guarded_sql(guard)
    latency_ms = int((perf_counter() - state["started"]) * 1000)

    if (
        settings.query_cache_enabled
        and execution.status == "success"
        and state.get("cache_key")
    ):
        get_cache_service().set(
            state["cache_key"],
            {"execution": execution.model_dump(mode="json")},
        )

    return {
        "execution": execution,
        "latency_ms": latency_ms,
        "node_timings": _add_node_timing(state, "sql_execution", started),
    }


def _explain_sql_node(state: AnalysisGraphState) -> AnalysisGraphState:
    """Guard 之后先查结果缓存；未命中再做受限 EXPLAIN。

    缓存命中时跳过 EXPLAIN 和数据库主查询，直接复用已验证的成功结果。
    EXPLAIN 失败时以执行错误状态进入有限修复而非主查询。
    """
    started = perf_counter()
    guard = state["guard"]
    cache_key: str | None = None

    if settings.query_cache_enabled:
        cache_key = build_query_cache_key(
            final_sql=guard.final_sql or state.get("selected_sql", ""),
            query_plan=state.get("question_intent", {}).get("query_plan"),
            app_user_id=state.get("app_user_id"),
            resolved_contracts=state.get("question_intent", {}).get("resolved_contracts"),
        )
        cached = get_cache_service().get(cache_key)
        if isinstance(cached, dict) and "execution" in cached:
            execution = SqlExecutionResult.model_validate(cached["execution"])
            return {
                "execution": execution,
                "cache_key": cache_key,
                "cache_hit": True,
                "explain": SqlExplainResult(status="success", latency_ms=0),
                "node_timings": _add_node_timing(state, "sql_explain", started),
            }

    explain = explain_guarded_sql(guard)
    updates: AnalysisGraphState = {
        "explain": explain,
        "cache_key": cache_key,
        "cache_hit": False,
        "node_timings": _add_node_timing(state, "sql_explain", started),
    }
    if explain.status != "success":
        updates["execution"] = SqlExecutionResult(
            status="error",
            latency_ms=explain.latency_ms,
            error_message=explain.error_message,
            error_category=explain.error_category or "explain_failed",
            user_error_message=explain.user_error_message,
        )
        updates["latency_ms"] = int((perf_counter() - state["started"]) * 1000)
    return updates


def _memory_update_work(state: AnalysisGraphState) -> Any:
    """记忆写回（成功沉淀 / 失败降级）。返回 updated_memory_id 供日志使用。"""
    execution = state["execution"]
    guard = state["guard"]
    selected_sql = state["selected_sql"]
    generated_sql = state["generated_sql"]
    reuse_plan = state["reuse_plan"]

    # 复用已验证记忆却执行失败：打断状态机并降级（计划 1a 的降级臂）。
    if (
        execution.status != "success"
        and generated_sql.path == "memory_reuse_verified"
        and reuse_plan.selected_memory_id is not None
    ):
        SqlMemoryRepository().record_failure(
            reuse_plan.selected_memory_id,
            reason=execution.error_category or "execution_failure",
        )
        return None

    if execution.status != "success" or not guard.allowed:
        return None

    query_spec = _query_spec_from_intent(state.get("question_intent"))
    updated_memory = upsert_successful_sql_memory(
        question=state["question"],
        sql_template=guard.final_sql or selected_sql,
        final_sql=guard.final_sql or selected_sql,
        parameters={
            "generation_path": generated_sql.path,
            "model_provider": generated_sql.model_provider,
            "model_name": generated_sql.model_name,
        },
        tables=sorted(_extract_sql_tables(guard.final_sql or selected_sql)),
        metrics=query_spec.metrics if query_spec else state["metric_names"],
        dimensions=query_spec.dimensions if query_spec else [],
        result_columns=execution.columns,
        row_count=execution.row_count,
        latency_ms=execution.latency_ms,
        context_fingerprints=build_sql_memory_context_fingerprints(
            state["retrieval_context"],
            state.get("question_intent", {}).get("resolved_contracts", []),
        ),
        question_vector=state.get("question_vector"),
    )
    return updated_memory.id


def _bookkeeping_node(state: AnalysisGraphState) -> AnalysisGraphState:
    """响应之后的簿记：记忆写回 + 运行日志。

    BOOKKEEPING_ASYNC=true 时提交后台线程（不阻塞响应）；
    false 时同步执行（测试与需要强一致的场景）。
    """
    started = perf_counter()
    snapshot: AnalysisGraphState = dict(state)

    def _work() -> None:
        updated_memory_id = _memory_update_work(snapshot)
        _log_run_work(snapshot, updated_memory_id)

    if settings.bookkeeping_async:
        submit_bookkeeping(_work, description="analysis bookkeeping")
    else:
        _work()
    return {"node_timings": _add_node_timing(state, "bookkeeping_dispatch", started)}


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
    result_contract = build_result_contract(
        state.get("original_question", state["question"]),
        presented_execution,
        state.get("question_intent", {}).get("query_plan", {}),
        guard.warnings,
    )
    response = present_sales_trend_result(
        question=state["question"],
        sql=guard.final_sql or selected_sql,
        execution=presented_execution,
        guard_warnings=guard.warnings,
        latency_ms=state["latency_ms"],
        retrieval_context=state["retrieval_context"],
        reuse_plan=state["reuse_plan"],
        result_contract=result_contract,
    )
    # run_id 随响应返回：评测与前端不再靠"问题文本匹配最近 run"这种脆弱关联（计划 4d）。
    response = response.model_copy(update={"run_id": state.get("run_id")})
    return {
        "response": response,
        "node_timings": _add_node_timing(state, "present_result", started),
    }


def _log_run_work(state: AnalysisGraphState, updated_memory_id: Any) -> None:
    guard = state["guard"]
    execution = state["execution"]
    retrieval_context = state["retrieval_context"]
    reuse_plan = state["reuse_plan"]
    generated_sql = state["generated_sql"]
    selected_sql = state["selected_sql"]
    _log_analysis_run(
        run_id=state.get("run_id"),
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
        model_provider=generated_sql.model_provider,
        model_name=generated_sql.model_name,
        model_latency_ms=generated_sql.model_latency_ms,
        generated_sql_text=selected_sql,
        sql_candidates=state.get("sql_candidates", []),
        updated_memory_id=updated_memory_id,
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
        explain=state.get("explain"),
        cache_hit=bool(state.get("cache_hit")),
        node_timings=state.get("node_timings", {}),
    )


def _log_analysis_run(
    *,
    run_id: UUID | None = None,
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
    model_provider: str = "",
    model_name: str = "",
    model_latency_ms: int = 0,
    generated_sql_text: str,
    sql_candidates: list[dict[str, Any]],
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
    explain: SqlExplainResult | None,
    cache_hit: bool,
    node_timings: dict[str, int],
) -> None:
    logger = QueryRunLogger()
    run = logger.log_run(
        run_id=run_id,
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
    tool_calls: list[dict[str, Any]] = [
        {
            "tool_name": "sql_memory_tools.retrieve_sql_memory",
            "input_payload": {"question": question},
            "output_payload": {"candidate_count": memory_candidate_count},
            "status": "success",
            "latency_ms": node_timings.get("memory_retrieval_and_plan", 0),
        },
        {
            "tool_name": "sql_memory_tools.plan_sql_reuse",
            "input_payload": {"candidate_count": memory_candidate_count},
            "output_payload": {
                "path_type": reuse_plan.path_type,
                "reuse_type": reuse_plan.reuse_type,
                "memory_hit": reuse_plan.memory_hit,
                "score": reuse_plan.score,
            },
            "status": "success",
            "latency_ms": node_timings.get("memory_retrieval_and_plan", 0),
        },
        {
            "tool_name": "context_builder.build_retrieval_context",
            "input_payload": {"question": question},
            "output_payload": {
                "metric_count": metric_count,
                "schema_column_count": schema_column_count,
                "relationship_count": relationship_count,
                "tables": context_tables,
                "fields_sample": context_fields[:20],
                "rerank_diagnostics": rerank_diagnostics,
            },
            "status": "success",
            "latency_ms": node_timings.get("context_retrieval", 0),
        },
        {
            "tool_name": "analysis_graph.select_generated_sql",
            "input_payload": {"path_type": reuse_plan.path_type},
            "output_payload": {
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
                # 候选 SQL 仅落在既有管理员运行详情中，便于定位模型与 Repair 偏差；不记录推理或原始模型文本。
                "sql_candidates": sql_candidates,
                "model_route": {
                    "provider": model_provider,
                    "model": model_name,
                    "latency_ms": model_latency_ms,
                },
            },
            "status": "success",
            "latency_ms": node_timings.get("sql_generation", 0),
        },
        {
            "tool_name": "sql_validation_tools.guard_sql",
            "input_payload": {"max_rows": 30},
            "output_payload": {
                "guard_status": guard_status,
                "warning_count": len(guard_warnings),
                "warnings": guard_warnings[:5],
                "error_count": len(guard_errors),
                "errors": guard_errors[:5],
            },
            "status": "success" if guard_status == "allowed" else "blocked",
            "latency_ms": node_timings.get("sql_guard", 0),
        },
        {
            "tool_name": "sql_execution_tools.explain_guarded_sql",
            "input_payload": {"guard_status": guard_status},
            "output_payload": {
                "explain_status": explain.status if explain else "skipped",
                "error_category": explain.error_category if explain else None,
                "cache_hit": cache_hit,
            },
            "status": explain.status if explain else "skipped",
            "latency_ms": node_timings.get("sql_explain", 0),
        },
        {
            "tool_name": "sql_execution_tools.execute_guarded_sql",
            "input_payload": {"guard_status": guard_status},
            "output_payload": {
                "execution_status": execution_status,
                "row_count": row_count,
                "cache_hit": cache_hit,
            },
            "status": execution_status,
            "latency_ms": node_timings.get("sql_execution", 0),
        },
        {
            "tool_name": "analysis_presenter.present_sales_trend_result",
            "input_payload": {"row_count": row_count},
            "output_payload": {"response_status": "success" if not error_message else "error"},
            "status": "success" if not error_message else "error",
            "latency_ms": node_timings.get("present_result", 0),
        },
        {
            "tool_name": "sql_memory_tools.upsert_successful_sql_memory",
            "input_payload": {"memory_hit": memory_hit},
            "output_payload": {"updated_memory_id": str(updated_memory_id) if updated_memory_id else None},
            "status": "success" if updated_memory_id else "skipped",
            "latency_ms": node_timings.get("memory_update", 0),
        },
        {
            "tool_name": "analysis_graph.pipeline_timings",
            "input_payload": {"question": question},
            "output_payload": {
                "node_timings_ms": node_timings,
                "total_latency_ms": latency_ms,
                "slowest_node": _slowest_node(node_timings),
            },
            "status": "success",
            "latency_ms": latency_ms,
        },
    ]
    logger.log_tool_calls(query_run_id=run.id, tool_calls=tool_calls)


def _sql_candidate(stage: str, generated: GeneratedSql) -> dict[str, Any]:
    """保留可审计 SQL 候选的最小诊断字段，避免记录模型推理和 Prompt。"""
    return {
        "stage": stage,
        "path": generated.path,
        "sql": generated.sql,
        "warning_count": len(generated.warnings),
    }


def _select_generated_sql(
    *,
    question: str,
    retrieval_context: RetrievalContext,
    reuse_plan: SqlReusePlan,
    adapter: ModelAdapter | None = None,
    model_enabled: bool | None = None,
    repair_context: dict[str, Any] | None = None,
    question_intent: dict[str, Any] | None = None,
    few_shot_examples: list[dict[str, str]] | None = None,
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
        few_shot_examples=few_shot_examples,
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


def _select_generated_sql_compat(**kwargs) -> GeneratedSql:
    """兼容旧签名的测试替身：逐个剥离其不认识的新增关键字参数。"""
    optional_kwargs = ("few_shot_examples", "question_intent")
    try:
        return _select_generated_sql(**kwargs)
    except TypeError as exc:
        if not any(name in str(exc) for name in optional_kwargs):
            raise
        fallback_kwargs = dict(kwargs)
        fallback_kwargs.pop("few_shot_examples", None)
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
    # Query Plan 存在时，必需表由 Inspector 按 plan.entities 精确检查；
    # 召回上下文的过度召回不应再强迫 SQL JOIN 无关表（与提示词"不要仅因其存在而 JOIN"一致）。
    if _query_spec_from_intent(question_intent) is None:
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
        if not _token_present(token, observed["text"], observed):
            warnings.append(f"{subject} 缺少当前问题需要的指标口径：{token}")
    for token in required["required_dimension_tokens"]:
        if not _token_present(token, observed["text"], observed):
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


# 依赖 COUNT(DISTINCT table.column) 语义（经 AST 别名解析）判定的指标口径：
# 不再依赖写死的 u./o. 表别名，任何别名的等价 SQL 均可通过校验。
_COUNT_DISTINCT_TOKEN_COLUMNS = {
    "new_user_count": {"users.id"},
    "ordering_user_count": {"orders.user_id"},
    "purchase_count": {"orders.id"},
}


def _token_present(token: str, lowered_sql: str, features: dict[str, Any] | None = None) -> bool:
    aliases = {
        "repeat": ["repeat", "repeat_rate", "paid_order_count"],
        "product": ["product", "product_id", "product_label"],
        "category": ["category", "category_label"],
        "payment_method": ["payment_method", "payment_type", "payment_method_label"],
        "date": ["date", "order_date", "created_at", "date_trunc('day'"],
        "month": ["month", "order_month", "date_trunc('month'"],
        "total_amount": ["total_amount", "sales_amount", "daily_sales", "gmv"],
        "new_user_count": ["new_user_count", "new_users"],
        "ordering_user_count": ["ordering_user_count", "order_user_count"],
        "purchase_count": ["purchase_count", "order_count"],
        "conversion_rate": ["conversion_rate", "conversion", "convert_rate"],
        "coupon_redemption_rate": ["coupon_redemption_rate", "redemption_rate", "redeem_rate"],
        "source": ["source", "traffic_source", "channel"],
        "user": ["user", "user_id", "user_label"],
        "coupon": ["coupon", "coupon_id", "coupon_code"],
    }
    if any(alias in lowered_sql for alias in aliases.get(token, [token])):
        return True
    semantic_columns = _COUNT_DISTINCT_TOKEN_COLUMNS.get(token)
    if semantic_columns:
        count_distinct = (features or {}).get("count_distinct")
        if count_distinct is None:
            count_distinct = _count_distinct_columns(lowered_sql)
        if semantic_columns & set(count_distinct):
            return True
    return False


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
        "count_distinct": _count_distinct_columns(sql),
    }


def _count_distinct_columns(sql: str) -> set[str]:
    """提取 COUNT(DISTINCT ...) 内引用的列，并把别名解析回真实表名。

    返回形如 {"orders.id", "users.id"} 的集合，供指标口径校验使用，
    避免把表别名写死成 u./o. 造成对正确 SQL 的误报。
    """
    if not sql.strip():
        return set()
    try:
        expression = parse_one(sql, dialect="postgres")
    except ParseError:
        return set()
    alias_to_table = {
        table.alias_or_name: table.name
        for table in expression.find_all(exp.Table)
        if table.name
    }
    alias_to_table.update(
        {table.name: table.name for table in expression.find_all(exp.Table) if table.name}
    )
    sole_table = next(iter(set(alias_to_table.values())), "") if len(set(alias_to_table.values())) == 1 else ""

    columns: set[str] = set()
    for count in expression.find_all(exp.Count):
        target = count.this
        if not isinstance(target, exp.Distinct):
            continue
        for column in target.find_all(exp.Column):
            table_name = alias_to_table.get(column.table or "", "" if column.table else sole_table)
            if table_name and column.name:
                columns.add(f"{table_name}.{column.name}".lower())
            elif column.name:
                columns.add(column.name.lower())
    return columns


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
    """接受 PostgreSQL 等价日期写法，仍要求半开区间的两个端点。

    先用 sqlglot 规范化（'x'::date 等价写法统一渲染为 CAST），再匹配：
    - col >= start AND col < end（含操作数反序 start <= col / end > col）
    - col BETWEEN start AND end（闭区间，视为满足两个端点）
    """
    if not sql.strip() or not start or not end:
        return False
    lowered = _normalized_lower_sql(sql)
    start_literal = _postgres_date_literal_pattern(start)
    end_literal = _postgres_date_literal_pattern(end)
    between = re.search(
        r"between\s+" + start_literal + r".{0,40}?\s+and\s+" + end_literal,
        lowered,
        flags=re.DOTALL,
    )
    if between:
        return True
    has_start = re.search(r">=\s*" + start_literal, lowered) or re.search(
        start_literal + r"\s*<=", lowered
    )
    has_end = re.search(r"<\s*" + end_literal, lowered) or re.search(
        end_literal + r"\s*>", lowered
    )
    return bool(has_start and has_end)


def _normalized_lower_sql(sql: str) -> str:
    """sqlglot 规范化后转小写；解析失败时退回原文本。"""
    try:
        return parse_one(sql, dialect="postgres").sql(dialect="postgres").lower()
    except (ParseError, Exception):  # noqa: BLE001 - 校验器不能因方言差异而崩溃
        return sql.lower()


def _postgres_date_literal_pattern(value: str) -> str:
    escaped = re.escape(value.lower())
    return (
        r"(?:date\s+['\"]" + escaped + r"['\"]"
        + r"|cast\s*\(\s*['\"]" + escaped + r"['\"]\s+as\s+(?:date|timestamp(?:\s+without\s+time\s+zone)?)\s*\)"
        + r"|['\"]" + escaped + r"['\"])"
    )


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
