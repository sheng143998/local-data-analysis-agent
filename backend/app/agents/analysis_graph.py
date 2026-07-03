from time import perf_counter

from backend.app.schemas.analysis import AnalyzeResponse
from backend.app.tools.analysis_presenter import present_sales_trend_result
from backend.app.tools.context_builder import build_retrieval_context
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
    """V1 real slice：先召回业务上下文，再执行真实 SQL Guard + Executor。"""
    started = perf_counter()
    retrieval_context = build_retrieval_context(question)
    guard = guard_sql(SALES_TREND_SQL, max_rows=30)
    execution = execute_guarded_sql(guard)
    latency_ms = int((perf_counter() - started) * 1000)
    return present_sales_trend_result(
        question=question,
        sql=guard.final_sql or SALES_TREND_SQL,
        execution=execution,
        guard_warnings=guard.warnings,
        latency_ms=latency_ms,
        retrieval_context=retrieval_context,
    )
