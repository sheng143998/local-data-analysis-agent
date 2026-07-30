"""记忆优先快路径（计划 2a，GRAPH_MEMORY_FIRST）。

重复问题不应该重新付一遍意图 LLM + 检索 + 生成的成本。命中条件刻意保守：
归一化问题**精确匹配** + trust_status=verified。近似命中仍走完整管线。

安全性不依赖指纹快照：命中 SQL 依旧经过 Guard（实时对照 schema_metadata
校验字段与白名单）→ EXPLAIN 预检 → 只读事务执行；schema 漂移会让 Guard
或执行失败，此时记录失败、降级记忆并回退到完整管线。
"""
from __future__ import annotations

import logging
from time import perf_counter
from typing import Any
from uuid import UUID, uuid4

from backend.app.core.background import submit_bookkeeping
from backend.app.core.config import settings
from backend.app.db.repositories.memory_repository import SqlMemoryRepository
from backend.app.schemas.analysis import AnalyzeResponse
from backend.app.schemas.memories import SqlMemoryRecord, SqlReusePlan
from backend.app.schemas.retrieval import RetrievalContext
from backend.app.tools.analysis_presenter import present_sales_trend_result
from backend.app.tools.result_contract_builder import build_result_contract
from backend.app.tools.run_logger import QueryRunLogger
from backend.app.tools.sql_execution_tools import execute_guarded_sql, explain_guarded_sql
from backend.app.tools.sql_validation_tools import guard_sql
from backend.app.tools.text_normalization import normalize_question

logger = logging.getLogger("backend.memory_fast_path")


def try_memory_fast_path(
    question: str,
    *,
    app_user_id: UUID | None = None,
    repository: SqlMemoryRepository | None = None,
) -> AnalyzeResponse | None:
    """精确命中已验证记忆时直接执行；任何一步不满足都返回 None 回退完整管线。"""
    if not settings.graph_memory_first:
        return None
    repo = repository or SqlMemoryRepository()
    try:
        memory = repo.get_by_normalized_question(normalize_question(question))
    except Exception:  # noqa: BLE001 - 快路径任何故障都不能挡住主管线
        logger.warning("memory fast path lookup failed", exc_info=True)
        return None
    if memory is None or memory.trust_status != "verified" or not memory.final_sql.strip():
        return None

    started = perf_counter()
    run_id = uuid4()
    timings: dict[str, int] = {}

    def _mark(name: str, node_started: float) -> None:
        timings[name] = int((perf_counter() - node_started) * 1000)

    node_started = perf_counter()
    guard = guard_sql(memory.final_sql, max_rows=settings.sql_max_rows)
    _mark("sql_guard", node_started)
    if not guard.allowed:
        _record_fast_path_failure(repo, memory, reason="guard_blocked")
        return None

    node_started = perf_counter()
    explain = explain_guarded_sql(guard)
    _mark("sql_explain", node_started)
    if explain.status != "success":
        _record_fast_path_failure(repo, memory, reason=explain.error_category or "explain_failed")
        return None

    node_started = perf_counter()
    execution = execute_guarded_sql(guard)
    _mark("sql_execution", node_started)
    if execution.status != "success":
        _record_fast_path_failure(repo, memory, reason=execution.error_category or "execution_failure")
        return None

    latency_ms = int((perf_counter() - started) * 1000)
    reuse_plan = SqlReusePlan(
        path_type="fast_path",
        reuse_type="direct_reuse",
        memory_hit=True,
        selected_memory_id=memory.id,
        selected_sql=memory.final_sql,
        candidate_count=1,
        score=1.0,
    )
    retrieval_context = RetrievalContext(
        tables=list(memory.tables),
        fields=[],
        metric_summary="命中已验证查询，直接复用历史口径",
    )
    node_started = perf_counter()
    result_contract = build_result_contract(question, execution, {}, guard.warnings)
    response = present_sales_trend_result(
        question=question,
        sql=guard.final_sql or memory.final_sql,
        execution=execution,
        guard_warnings=guard.warnings,
        latency_ms=latency_ms,
        retrieval_context=retrieval_context,
        reuse_plan=reuse_plan,
        result_contract=result_contract,
    )
    _mark("present_result", node_started)
    response = response.model_copy(update={"run_id": run_id, "path": "fast_path"})

    def _bookkeeping() -> None:
        _log_fast_path_run(
            run_id=run_id,
            app_user_id=app_user_id,
            question=question,
            memory=memory,
            final_sql=guard.final_sql or memory.final_sql,
            execution_row_count=execution.row_count,
            latency_ms=latency_ms,
            timings=dict(timings),
        )
        # 成功复用也计入状态机统计（verified 记忆仅更新使用统计，不改写 SQL）。
        _record_fast_path_success(repo, memory, execution.latency_ms)

    if settings.bookkeeping_async:
        submit_bookkeeping(_bookkeeping, description="fast path bookkeeping")
    else:
        _bookkeeping()
    return response


def _record_fast_path_failure(repo: SqlMemoryRepository, memory: SqlMemoryRecord, *, reason: str) -> None:
    try:
        repo.record_failure(memory.id, reason=f"fast_path:{reason}")
    except Exception:  # noqa: BLE001
        logger.warning("fast path failure bookkeeping failed", exc_info=True)


def _record_fast_path_success(repo: SqlMemoryRepository, memory: SqlMemoryRecord, latency_ms: int) -> None:
    try:
        from backend.app.schemas.memories import SqlMemoryUpsert

        repo.upsert_success(
            SqlMemoryUpsert(
                canonical_question=memory.canonical_question,
                sql_template=memory.sql_template,
                final_sql=memory.final_sql,
                parameters=memory.parameters,
                tables=memory.tables,
                metrics=memory.metrics,
                dimensions=memory.dimensions,
                result_columns=memory.last_result_columns,
                row_count=memory.last_row_count,
                latency_ms=latency_ms,
                trust_status="verified",
                filters={key: value for key, value in memory.filters.items() if key != "trust_status"},
            )
        )
    except Exception:  # noqa: BLE001
        logger.warning("fast path success bookkeeping failed", exc_info=True)


def _log_fast_path_run(
    *,
    run_id: UUID,
    app_user_id: UUID | None,
    question: str,
    memory: SqlMemoryRecord,
    final_sql: str,
    execution_row_count: int,
    latency_ms: int,
    timings: dict[str, int],
) -> None:
    try:
        logger_service = QueryRunLogger()
        run = logger_service.log_run(
            run_id=run_id,
            app_user_id=app_user_id,
            user_question=question,
            rewritten_question=question,
            generated_sql=final_sql,
            final_sql=final_sql,
            guard_status="allowed",
            execution_status="success",
            row_count=execution_row_count,
            latency_ms=latency_ms,
            memory_hit=True,
            memory_id=memory.id,
        )
        tool_calls: list[dict[str, Any]] = [
            {
                "tool_name": "memory_fast_path.exact_verified_hit",
                "input_payload": {"question": question},
                "output_payload": {"memory_id": str(memory.id), "trust_status": memory.trust_status},
                "status": "success",
                "latency_ms": 0,
            },
            *[
                {
                    "tool_name": f"memory_fast_path.{name}",
                    "input_payload": {},
                    "output_payload": {},
                    "status": "success",
                    "latency_ms": duration,
                }
                for name, duration in timings.items()
            ],
            {
                "tool_name": "analysis_graph.pipeline_timings",
                "input_payload": {"question": question},
                "output_payload": {
                    "node_timings_ms": timings,
                    "total_latency_ms": latency_ms,
                    "path": "fast_path_exact",
                },
                "status": "success",
                "latency_ms": latency_ms,
            },
        ]
        logger_service.log_tool_calls(query_run_id=run.id, tool_calls=tool_calls)
    except Exception:  # noqa: BLE001
        logger.warning("fast path run logging failed", exc_info=True)
