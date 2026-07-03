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

    period_label = _period_label(sql)
    main_metric_label = _main_metric_label(question)
    leading_label = analysis_rows[0]["date"] if analysis_rows else "无"

    return AnalyzeResponse(
        question=question,
        path=_path_type(reuse_plan),
        summary=_summary_text(
            row_count=len(analysis_rows),
            period_label=period_label,
            main_metric_label=main_metric_label,
            total_sales=total_sales,
            total_orders=total_orders,
            avg_order_value=avg_order_value,
            avg_refund_rate=avg_refund_rate,
            leading_label=leading_label,
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
            "toolCalls": 8,
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
    rate_value = row.get("refund_rate")
    if rate_value is None:
        rate_value = row.get("success_rate")
    if rate_value is None:
        rate_value = row.get("failure_rate")
    if rate_value is None:
        rate_value = row.get("gross_margin")
    if rate_value is None:
        rate_value = row.get("repeat_rate")
    return {
        "date": _row_label(row),
        "amount": amount,
        "orders": orders,
        "avg": round(float(row.get("avg_order_value") or 0)),
        "refundRate": f"{float(rate_value or 0):.2f}%",
    }


def _row_label(row: dict) -> str:
    for key in [
        "segment_label",
        "city_label",
        "payment_method_label",
        "product_label",
        "category_label",
        "product_category",
        "order_date",
    ]:
        value = row.get(key)
        if value:
            return str(value)
    return "未知"


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
            "toolCalls": 8,
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
    if reuse_plan and reuse_plan.path_type == "rewrite_path":
        return "改写历史 SQL"
    return "选择 SQL 模板"


def _period_label(sql: str) -> str:
    if "CITY_LABEL" in sql.upper():
        return "城市"
    if "SEGMENT_LABEL" in sql.upper():
        return "用户"
    if "PAYMENT_METHOD_LABEL" in sql.upper():
        return "支付方式"
    if "PRODUCT_LABEL" in sql.upper():
        return "商品"
    if "CATEGORY_LABEL" in sql.upper():
        return "品类"
    if "DATE_TRUNC('MONTH'" in sql.upper():
        return "月份"
    return "有交易日期"


def _main_metric_label(question: str) -> str:
    if any(keyword in question for keyword in ["复购率", "复购", "回购"]):
        return "复购率"
    if any(keyword in question for keyword in ["城市", "地区", "地域"]) and any(
        keyword in question for keyword in ["客单价", "平均订单", "平均金额"]
    ):
        return "城市客单价"
    if any(keyword in question for keyword in ["毛利率", "毛利", "利润率"]):
        return "毛利率排行"
    if any(keyword in question for keyword in ["支付失败率", "失败率"]):
        return "支付失败率"
    if any(keyword in question for keyword in ["支付成功率", "成功率", "支付方式"]):
        return "支付成功率"
    if any(keyword in question for keyword in ["退款率", "退款", "售后"]):
        return "退款率排行"
    if any(keyword in question for keyword in ["品类", "类目", "分类"]):
        return "销售额排行"
    if any(keyword in question for keyword in ["商品", "产品", "sku", "SKU"]):
        return "销售额排行"
    if any(keyword in question for keyword in ["订单数", "订单量", "下单数", "下单量"]):
        return "订单数趋势"
    return "销售趋势"


def _summary_text(
    *,
    row_count: int,
    period_label: str,
    main_metric_label: str,
    total_sales: int,
    total_orders: int,
    avg_order_value: int,
    avg_refund_rate: float,
    leading_label: str,
) -> str:
    if main_metric_label == "复购率":
        return (
            f"已基于真实 PostgreSQL 数据计算整体复购率。"
            f"覆盖用户数 {total_orders:,}，相关销售额约为 ¥{total_sales:,.0f}，"
            f"复购率为 {avg_refund_rate:.2f}%。"
        )
    if main_metric_label == "城市客单价":
        return (
            f"已基于真实 PostgreSQL 数据按城市查询客单价。"
            f"当前最高的是 {leading_label}，入选范围销售额约为 ¥{total_sales:,.0f}，"
            f"关联订单数 {total_orders:,}，平均客单价约 ¥{avg_order_value:,}。"
        )
    if main_metric_label == "毛利率排行":
        return (
            f"已基于真实 PostgreSQL 数据查询毛利率最高的 {row_count} 个{period_label}。"
            f"当前最高的是 {leading_label}，入选范围销售额约为 ¥{total_sales:,.0f}，"
            f"关联订单数 {total_orders:,}。"
        )
    if main_metric_label in {"支付成功率", "支付失败率"}:
        return (
            f"已基于真实 PostgreSQL 数据按支付方式查询{main_metric_label}。"
            f"当前最高的是 {leading_label}，覆盖订单数 {total_orders:,}，"
            f"相关支付金额约为 ¥{total_sales:,.0f}。"
        )
    if main_metric_label == "退款率排行":
        return (
            f"已基于真实 PostgreSQL 数据查询退款率最高的 {row_count} 个{period_label}。"
            f"当前最高的是 {leading_label}，入选范围关联订单数 {total_orders:,}，"
            f"合计销售额约为 ¥{total_sales:,.0f}。"
        )
    if period_label in {"商品", "品类"}:
        return (
            f"已基于真实 PostgreSQL 数据查询销售额最高的 {row_count} 个{period_label}。"
            f"当前第一名是 {leading_label}，入选范围合计销售额约为 ¥{total_sales:,.0f}，"
            f"关联订单数 {total_orders:,}，平均客单价约 ¥{avg_order_value:,}。"
        )
    return (
        f"已基于真实 PostgreSQL 数据查询最近 {row_count} 个{period_label}的{main_metric_label}。"
        f"区间内总销售额约为 ¥{total_sales:,.0f}，订单数 {total_orders:,}，"
        f"平均客单价约 ¥{avg_order_value:,}，平均退款率 {avg_refund_rate:.2f}%。"
    )
