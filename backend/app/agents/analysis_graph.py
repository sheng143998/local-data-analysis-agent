from time import perf_counter

from backend.app.schemas.analysis import AnalyzeResponse
from backend.app.schemas.memories import SqlReusePlan
from backend.app.tools.analysis_presenter import present_sales_trend_result
from backend.app.tools.context_builder import build_retrieval_context
from backend.app.tools.run_logger import QueryRunLogger
from backend.app.tools.sql_memory_tools import (
    plan_sql_reuse,
    retrieve_sql_memory,
    upsert_successful_sql_memory,
)
from backend.app.tools.sql_execution_tools import execute_guarded_sql
from backend.app.tools.sql_validation_tools import guard_sql


SALES_TREND_SQL = """
SELECT
  DATE(o.created_at) AS order_date,
  SUM(o.total_amount) AS daily_sales,
  COUNT(DISTINCT o.id) AS order_count,
  ROUND(SUM(o.total_amount) / NULLIF(COUNT(DISTINCT o.id), 0), 2) AS avg_order_value,
  ROUND(COUNT(DISTINCT r.id)::numeric / NULLIF(COUNT(DISTINCT o.id), 0) * 100, 2) AS refund_rate
FROM orders o
LEFT JOIN payments p ON p.order_id = o.id
LEFT JOIN refunds r ON r.order_id = o.id
WHERE o.created_at IS NOT NULL
  AND p.status = 'paid'
GROUP BY DATE(o.created_at)
ORDER BY order_date DESC
LIMIT 30
"""


def run_analysis_graph(question: str) -> AnalyzeResponse:
    """V1 real slice：先检索 SQL Memory，再执行真实 SQL Guard + Executor。"""
    started = perf_counter()
    retrieval_context = build_retrieval_context(question)
    metric_names = [metric.metric_name for metric in retrieval_context.metrics]
    memory_candidates = retrieve_sql_memory(
        question,
        metrics=metric_names,
        tables=retrieval_context.tables,
    )
    reuse_plan = plan_sql_reuse(memory_candidates)
    selected_sql = reuse_plan.selected_sql or SALES_TREND_SQL

    guard = guard_sql(selected_sql, max_rows=30)
    execution = execute_guarded_sql(guard)
    latency_ms = int((perf_counter() - started) * 1000)
    updated_memory_id = None
    if execution.status == "success" and guard.allowed:
        updated_memory = upsert_successful_sql_memory(
            question=question,
            sql_template=SALES_TREND_SQL,
            final_sql=guard.final_sql or selected_sql,
            tables=retrieval_context.tables,
            metrics=metric_names,
            result_columns=execution.columns,
            row_count=execution.row_count,
            latency_ms=execution.latency_ms,
        )
        updated_memory_id = updated_memory.id

    response = present_sales_trend_result(
        question=question,
        sql=guard.final_sql or selected_sql,
        execution=execution,
        guard_warnings=guard.warnings,
        latency_ms=latency_ms,
        retrieval_context=retrieval_context,
        reuse_plan=reuse_plan,
    )
    _log_analysis_run(
        question=question,
        final_sql=guard.final_sql or selected_sql,
        guard_status="allowed" if guard.allowed else "blocked",
        execution_status=execution.status,
        row_count=execution.row_count,
        latency_ms=latency_ms,
        memory_hit=reuse_plan.memory_hit,
        memory_id=reuse_plan.selected_memory_id,
        memory_candidate_count=len(memory_candidates),
        reuse_plan=reuse_plan,
        updated_memory_id=updated_memory_id,
        error_message=execution.error_message or "; ".join(guard.errors) or None,
        metric_count=len(retrieval_context.metrics),
        schema_column_count=len(retrieval_context.schema_columns),
    )
    return response


def _log_analysis_run(
    *,
    question: str,
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
    error_message: str | None,
    metric_count: int,
    schema_column_count: int,
) -> None:
    logger = QueryRunLogger()
    run = logger.log_run(
        user_question=question,
        generated_sql=SALES_TREND_SQL,
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
    )
    logger.log_tool_call(
        query_run_id=run.id,
        tool_name="context_builder.build_retrieval_context",
        input_payload={"question": question},
        output_payload={
            "metric_count": metric_count,
            "schema_column_count": schema_column_count,
        },
        status="success",
    )
    logger.log_tool_call(
        query_run_id=run.id,
        tool_name="sql_validation_tools.guard_sql",
        input_payload={"max_rows": 30},
        output_payload={"guard_status": guard_status},
        status="success" if guard_status == "allowed" else "blocked",
    )
    logger.log_tool_call(
        query_run_id=run.id,
        tool_name="sql_execution_tools.execute_guarded_sql",
        input_payload={"guard_status": guard_status},
        output_payload={"execution_status": execution_status, "row_count": row_count},
        status=execution_status,
    )
    logger.log_tool_call(
        query_run_id=run.id,
        tool_name="analysis_presenter.present_sales_trend_result",
        input_payload={"row_count": row_count},
        output_payload={"response_status": "success" if not error_message else "error"},
        status="success" if not error_message else "error",
    )
    logger.log_tool_call(
        query_run_id=run.id,
        tool_name="sql_memory_tools.upsert_successful_sql_memory",
        input_payload={"memory_hit": memory_hit},
        output_payload={"updated_memory_id": str(updated_memory_id) if updated_memory_id else None},
        status="success" if updated_memory_id else "skipped",
    )
