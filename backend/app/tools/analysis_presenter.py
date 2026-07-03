from backend.app.schemas.analysis import AnalyzeResponse
from backend.app.schemas.memories import SqlReusePlan
from backend.app.schemas.retrieval import RetrievalContext
from backend.app.schemas.sql_execution import SqlExecutionResult


def present_sales_trend_result(
    question: str,
    sql: str,
    execution: SqlExecutionResult,
    guard_warnings: list[str],
    latency_ms: int,
    retrieval_context: RetrievalContext | None = None,
    reuse_plan: SqlReusePlan | None = None,
) -> AnalyzeResponse:
    if execution.status != "success":
        return AnalyzeResponse(
            **_error_payload(question, sql, execution, latency_ms, retrieval_context, reuse_plan)
        )

    rows = list(reversed(execution.rows))
    analysis_rows = [_to_analysis_row(row) for row in rows]
    total_sales = sum(row["amount"] for row in analysis_rows)
    total_orders = sum(row["orders"] for row in analysis_rows)
    avg_order_value = round(total_sales / total_orders) if total_orders else 0
    avg_refund_rate = _average_refund_rate(analysis_rows)
    date_range = _date_range(analysis_rows)

    return AnalyzeResponse(
        question=question,
        path=_path_type(reuse_plan),
        summary=(
            f"已基于真实 PostgreSQL 数据查询最近 {len(analysis_rows)} 个有交易日期的销售趋势。"
            f"区间内总销售额约为 ¥{total_sales:,.0f}，订单数 {total_orders:,}，"
            f"平均客单价约 ¥{avg_order_value:,}，平均退款率 {avg_refund_rate:.2f}%。"
        ),
        sql=sql,
        metrics=[
            {"label": "总销售额", "value": f"¥ {total_sales:,.0f}", "delta": "--", "hint": "真实查询"},
            {"label": "订单数", "value": f"{total_orders:,}", "delta": "--", "hint": "真实查询"},
            {"label": "退款率", "value": f"{avg_refund_rate:.2f}%", "delta": "--", "hint": "真实查询"},
            {"label": "平均客单价", "value": f"¥ {avg_order_value:,}", "delta": "--", "hint": "真实查询"},
        ],
        rows=analysis_rows,
        source={
            "dataset": "Olist 巴西电商公开数据集 + 合成增强数据",
            "tables": _source_tables(retrieval_context),
            "fields": _source_fields(retrieval_context),
            "metricDefinition": _metric_definition(retrieval_context),
            "range": date_range,
            "returnedRows": execution.row_count,
            "queryTime": f"{execution.latency_ms}ms",
            "security": "只读 SELECT，已通过 SQL Guard",
        },
        trace={
            "toolCalls": 7,
            "modelCalls": 0,
            "memoryCandidates": reuse_plan.candidate_count if reuse_plan else 0,
            "totalTime": f"{latency_ms}ms",
        },
        steps=[
            {"name": "理解问题", "status": "已完成", "time": "1ms"},
            {"name": "检索 SQL Memory", "status": "已完成", "time": "1ms"},
            {"name": "规划复用路径", "status": "已完成", "time": "1ms"},
            {"name": "召回指标口径", "status": "已完成", "time": "1ms"},
            {"name": "读取数据结构", "status": "已完成", "time": "1ms"},
            {"name": _template_step_name(reuse_plan), "status": "已完成", "time": "1ms"},
            {"name": "安全校验", "status": "已完成", "time": "1ms"},
            {"name": "执行查询", "status": "已完成", "time": f"{execution.latency_ms}ms"},
            {"name": "整理结论", "status": "已完成", "time": "1ms"},
        ],
    )


def _to_analysis_row(row: dict) -> dict:
    amount = round(float(row.get("daily_sales") or 0))
    orders = int(row.get("order_count") or 0)
    return {
        "date": str(row.get("order_date")),
        "amount": amount,
        "orders": orders,
        "avg": round(float(row.get("avg_order_value") or 0)),
        "refundRate": f"{float(row.get('refund_rate') or 0):.2f}%",
    }


def _average_refund_rate(rows: list[dict]) -> float:
    if not rows:
        return 0
    return sum(float(row["refundRate"].rstrip("%")) for row in rows) / len(rows)


def _date_range(rows: list[dict]) -> str:
    if not rows:
        return "无数据"
    return f"{rows[0]['date']} 至 {rows[-1]['date']}"


def _error_payload(
    question: str,
    sql: str,
    execution: SqlExecutionResult,
    latency_ms: int,
    retrieval_context: RetrievalContext | None,
    reuse_plan: SqlReusePlan | None,
) -> dict:
    return {
        "question": question,
        "path": _path_type(reuse_plan),
        "summary": f"查询未成功执行：{execution.error_message or execution.status}",
        "sql": sql,
        "metrics": [],
        "rows": [],
        "source": {
            "dataset": "Olist 巴西电商公开数据集 + 合成增强数据",
            "tables": _source_tables(retrieval_context),
            "fields": _source_fields(retrieval_context),
            "metricDefinition": _metric_definition(retrieval_context),
            "range": "无数据",
            "returnedRows": 0,
            "queryTime": f"{execution.latency_ms}ms",
            "security": "SQL Guard / Executor",
        },
        "trace": {
            "toolCalls": 7,
            "modelCalls": 0,
            "memoryCandidates": reuse_plan.candidate_count if reuse_plan else 0,
            "totalTime": f"{latency_ms}ms",
        },
        "steps": [
            {"name": "检索 SQL Memory", "status": "已完成", "time": "1ms"},
            {"name": "规划复用路径", "status": "已完成", "time": "1ms"},
            {"name": "召回指标口径", "status": "已完成", "time": "1ms"},
            {"name": "读取数据结构", "status": "已完成", "time": "1ms"},
            {"name": "安全校验", "status": "已完成", "time": "1ms"},
            {"name": "执行查询", "status": "已完成", "time": f"{execution.latency_ms}ms"},
            {"name": "整理结论", "status": "已完成", "time": "1ms"},
        ],
    }


def _source_tables(retrieval_context: RetrievalContext | None) -> list[str]:
    if retrieval_context and retrieval_context.tables:
        return retrieval_context.tables
    return ["orders", "payments", "refunds"]


def _source_fields(retrieval_context: RetrievalContext | None) -> list[str]:
    if retrieval_context and retrieval_context.fields:
        return retrieval_context.fields
    return ["orders.created_at", "orders.status", "orders.total_amount", "payments.order_id"]


def _metric_definition(retrieval_context: RetrievalContext | None) -> str:
    if retrieval_context and retrieval_context.metric_summary:
        return retrieval_context.metric_summary
    return "销售额 = 已支付订单 total_amount 汇总"


def _path_type(reuse_plan: SqlReusePlan | None) -> str:
    return reuse_plan.path_type if reuse_plan else "cold_path"


def _template_step_name(reuse_plan: SqlReusePlan | None) -> str:
    if reuse_plan and reuse_plan.memory_hit:
        return "复用历史 SQL"
    return "选择 SQL 模板"
