from dataclasses import dataclass
from datetime import date, datetime
import re
from typing import Any

from backend.app.schemas.analysis import AnalyzeResponse, VisualizationSpec
from backend.app.schemas.memories import SqlReusePlan
from backend.app.schemas.retrieval import RetrievalContext
from backend.app.schemas.sql_execution import SqlExecutionResult
from backend.app.tools.question_intent_parser import ParsedQuestionIntent
from backend.app.schemas.result_contract import ResultContract
from backend.app.tools.result_contract_builder import build_visualization_spec


@dataclass(frozen=True)
class ResultProfile:
    row_count: int
    dimension_label: str
    dimension_value: str
    primary_metric_label: str
    primary_metric_value: str
    metrics: list[dict[str, str]]
    range_label: str


def present_sales_trend_result(
    question: str,
    sql: str,
    execution: SqlExecutionResult,
    guard_warnings: list[str],
    latency_ms: int,
    retrieval_context: RetrievalContext | None = None,
    reuse_plan: SqlReusePlan | None = None,
    result_contract: ResultContract | None = None,
) -> AnalyzeResponse:
    if execution.status != "success":
        return AnalyzeResponse(
            **_error_payload(question, sql, execution, latency_ms, retrieval_context, reuse_plan)
        )

    # 业务规则：结果行必须保留 Executor 的 SQL ORDER BY 顺序，Presenter 只能格式化，不能重排业务结果。
    rows = list(execution.rows)

    period_label = _period_label(sql)
    main_metric_label = _contract_metric_label(result_contract) or _main_metric_label(question)
    profile = _build_result_profile(
        rows=rows,
        columns=execution.columns,
        period_label=period_label,
        main_metric_label=main_metric_label,
    )
    result_state = result_contract.result_state if result_contract else ("empty" if execution.row_count == 0 else "success")

    return AnalyzeResponse(
        question=question,
        path=_path_type(reuse_plan),
        summary=_generic_summary_text(
            profile=profile,
            period_label=period_label,
            main_metric_label=main_metric_label,
        ),
        sql=sql,
        metrics=profile.metrics,
        rows=[_to_response_row(row) for row in rows],
        source={
            "dataset": "Olist 巴西电商公开数据集 + 合成增强数据",
            "tables": _source_tables(retrieval_context),
            "fields": _source_fields(retrieval_context),
            "metricDefinition": _metric_definition(retrieval_context),
            "range": profile.range_label,
            "returnedRows": execution.row_count,
            "resultState": result_state,
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
        visualization=build_visualization_spec(result_contract.model_copy(update={"rows": rows})) if result_contract else VisualizationSpec(),
    )


def present_clarification_response(
    question: str,
    intent: ParsedQuestionIntent,
    latency_ms: int,
) -> AnalyzeResponse:
    summary = intent.clarification or "我还不能确定你想查询的具体指标，请确认后我再继续。"
    return AnalyzeResponse(
        question=question,
        path="cold_path",
        summary=summary,
        sql="",
        metrics=[],
        rows=[],
        source={
            "dataset": "Olist 巴西电商公开数据集 + 合成增强数据",
            "tables": [],
            "fields": [],
            "metricDefinition": intent.normalized_question,
            "range": "等待用户确认",
            "returnedRows": 0,
            "resultState": "blocked",
            "queryTime": "0ms",
            "security": "未生成 SQL，等待用户确认",
        },
        trace={
            "toolCalls": 1,
            "modelCalls": 1 if intent.source == "llm" else 0,
            "memoryCandidates": 0,
            "totalTime": f"{latency_ms}ms",
        },
        steps=[
            {"name": "理解问题", "status": "已完成", "time": f"{latency_ms}ms"},
            {"name": "等待确认", "status": "已跳过", "time": "--"},
        ],
    )


def _to_response_row(row: dict) -> dict:
    return {str(key): _to_response_value(value) for key, value in row.items()}


def _to_response_value(value: Any) -> Any:
    # API 契约只传递 JSON 基础类型；数据库时间对象在此处序列化，业务排序保持不变。
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, date):
        return value.isoformat()
    return value


def _build_result_profile(
    *,
    rows: list[dict],
    columns: list[str],
    period_label: str,
    main_metric_label: str,
) -> ResultProfile:
    if not rows:
        return ResultProfile(
            row_count=0,
            dimension_label=period_label,
            dimension_value="无数据",
            primary_metric_label=main_metric_label,
            primary_metric_value="无数据",
            metrics=[_metric_card("返回行数", "0", "真实查询")],
            range_label="无数据",
        )

    ordered_columns = columns or list(rows[0].keys())
    dimension_column = _dimension_column(ordered_columns, rows)
    numeric_columns = _numeric_columns(ordered_columns, rows)
    primary_metric_column = _primary_metric_column(numeric_columns, main_metric_label)
    dimension_value = _display_value(rows[0].get(dimension_column)) if dimension_column else "首行"
    primary_metric_value = (
        _format_value(primary_metric_column, rows[0].get(primary_metric_column))
        if primary_metric_column
        else "无数值列"
    )
    metrics = _profile_metrics(rows, numeric_columns)
    range_label = _profile_range(rows, dimension_column, period_label)

    return ResultProfile(
        row_count=len(rows),
        dimension_label=_column_label(dimension_column) if dimension_column else period_label,
        dimension_value=dimension_value,
        primary_metric_label=_column_label(primary_metric_column) if primary_metric_column else main_metric_label,
        primary_metric_value=primary_metric_value,
        metrics=metrics,
        range_label=range_label,
    )


def _dimension_column(columns: list[str], rows: list[dict]) -> str | None:
    preferred_tokens = [
        "date",
        "month",
        "label",
        "name",
        "category",
        "city",
        "method",
        "segment",
        "product",
    ]
    for column in columns:
        lowered = column.lower()
        if any(token in lowered for token in preferred_tokens) and not _is_numeric_value(rows[0].get(column)):
            return column
    for column in columns:
        if not _is_numeric_value(rows[0].get(column)):
            return column
    return columns[0] if columns else None


def _numeric_columns(columns: list[str], rows: list[dict]) -> list[str]:
    numeric: list[str] = []
    for column in columns:
        values = [row.get(column) for row in rows if row.get(column) is not None]
        if values and all(_is_numeric_value(value) for value in values[:10]):
            numeric.append(column)
    return numeric


def _primary_metric_column(numeric_columns: list[str], main_metric_label: str) -> str | None:
    if not numeric_columns:
        return None
    preferred_by_metric = {
        "复购率": ["repeat_rate"],
        "城市客单价": ["avg_order_value"],
        "毛利率排行": ["gross_margin"],
        "支付失败率": ["failure_rate"],
        "支付成功率": ["success_rate"],
        "退款率排行": ["refund_rate"],
        "订单数趋势": ["order_count", "orders", "count"],
        "销售额排行": ["daily_sales", "sales_amount", "total_amount"],
        "销售趋势": ["daily_sales", "sales_amount", "total_amount"],
    }
    preferred_tokens = preferred_by_metric.get(main_metric_label, [])
    for token in preferred_tokens:
        for column in numeric_columns:
            if token in column.lower():
                return column
    return numeric_columns[0]


def _profile_metrics(rows: list[dict], numeric_columns: list[str]) -> list[dict[str, str]]:
    metrics: list[dict[str, str]] = [_metric_card("返回行数", f"{len(rows):,}", "真实查询")]
    for column in numeric_columns[:3]:
        values = [_to_float(row.get(column)) for row in rows if row.get(column) is not None]
        if not values:
            continue
        if _is_rate_column(column):
            value = sum(values) / len(values)
            hint = "平均值"
        elif _is_average_column(column):
            value = sum(values) / len(values)
            hint = "平均值"
        else:
            value = sum(values)
            hint = "合计"
        metrics.append(_metric_card(_column_label(column), _format_number(column, value), hint))
    return metrics[:4]


def _profile_range(rows: list[dict], dimension_column: str | None, period_label: str) -> str:
    if not rows:
        return "无数据"
    if dimension_column and _is_date_like_column(dimension_column):
        first = _display_value(rows[0].get(dimension_column))
        last = _display_value(rows[-1].get(dimension_column))
        return f"{first} 至 {last}"
    return f"{period_label}维度，返回 {len(rows)} 行"


def _generic_summary_text(
    *,
    profile: ResultProfile,
    period_label: str,
    main_metric_label: str,
) -> str:
    if profile.row_count <= 0:
        return f"已基于真实 PostgreSQL 数据执行{main_metric_label}查询；当前筛选条件下没有匹配记录。"
    return (
        f"已基于真实 PostgreSQL 数据查询{main_metric_label}，"
        f"按{period_label}返回 {profile.row_count} 行结果。"
        f"首行{profile.dimension_label}为 {profile.dimension_value}，"
        f"{profile.primary_metric_label}为 {profile.primary_metric_value}。"
    )


def _metric_card(label: str, value: str, hint: str) -> dict[str, str]:
    return {"label": label, "value": value, "delta": "--", "hint": hint}


def _column_label(column: str | None) -> str:
    if not column:
        return "指标"
    labels = {
        "order_date": "日期",
        "order_month": "月份",
        "month": "月份",
        "daily_sales": "销售额",
        "sales_amount": "销售额",
        "total_amount": "销售额",
        "order_count": "订单数",
        "avg_order_value": "客单价",
        "refund_rate": "退款率",
        "success_rate": "支付成功率",
        "failure_rate": "支付失败率",
        "gross_margin": "毛利率",
        "repeat_rate": "复购率",
        "payment_success_rate": "支付成功率",
        "payment_failure_rate": "支付失败率",
        "category_label": "品类",
        "product_label": "商品",
        "city_label": "城市",
        "payment_method_label": "支付方式",
        "segment_label": "用户分组",
    }
    return labels.get(column, column.replace("_", " "))


def _format_value(column: str | None, value: Any) -> str:
    if value is None:
        return "无"
    if column and _is_numeric_value(value):
        return _format_number(column, _to_float(value))
    return _display_value(value)


def _format_number(column: str | None, value: float) -> str:
    if column and _is_rate_column(column):
        # 业务规则：数据库比例按 0 到 1 返回，界面与摘要统一转换为百分数。
        return f"{value * 100:.2f}%"
    if column and _is_money_column(column):
        return f"¥ {value:,.0f}"
    if abs(value) >= 1000:
        return f"{value:,.0f}"
    if float(value).is_integer():
        return f"{value:.0f}"
    return f"{value:.2f}"


def _display_value(value: Any) -> str:
    if value is None:
        return "无"
    if isinstance(value, datetime):
        return value.date().isoformat()
    if isinstance(value, date):
        return value.isoformat()
    text = str(value)
    # PostgreSQL 时间维度可能经 API 序列化为 ISO 文本；摘要不应展示时区和零点时间。
    if re.match(r"^\d{4}-\d{2}-\d{2}T", text):
        return text[:10]
    return text


def _is_numeric_value(value: Any) -> bool:
    if isinstance(value, bool) or value is None:
        return False
    try:
        float(value)
    except (TypeError, ValueError):
        return False
    return True


def _to_float(value: Any) -> float:
    return float(value or 0)


def _is_rate_column(column: str) -> bool:
    lowered = column.lower()
    return any(token in lowered for token in ["rate", "ratio", "margin", "percent"])


def _is_money_column(column: str) -> bool:
    lowered = column.lower()
    return any(token in lowered for token in ["sales", "amount", "value", "price", "revenue", "gmv"])


def _is_average_column(column: str) -> bool:
    lowered = column.lower()
    return lowered.startswith("avg_") or "average" in lowered


def _is_date_like_column(column: str) -> bool:
    lowered = column.lower()
    return "date" in lowered or "month" in lowered


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
            "resultState": execution.status,
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
        return "校验并复用历史 SQL"
    if reuse_plan and reuse_plan.path_type == "rewrite_path":
        return "模型改写历史 SQL"
    return "模型生成 SQL"


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


def _contract_metric_label(contract: ResultContract | None) -> str:
    if not contract:
        return ""
    measures = contract.query_plan.get("measures", [])
    if not measures:
        return ""
    name = measures[0].get("name", "") if isinstance(measures[0], dict) else ""
    return _column_label(str(name))


