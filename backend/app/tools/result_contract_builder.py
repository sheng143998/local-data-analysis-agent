from backend.app.schemas.analysis import VisualizationSpec
from backend.app.schemas.result_contract import ResultColumn, ResultContract
from backend.app.schemas.sql_execution import SqlExecutionResult


def build_result_contract(question: str, execution: SqlExecutionResult, query_plan: dict | None, warnings: list[str]) -> ResultContract:
    plan = query_plan or {}
    measures = {item.get("name") for item in plan.get("measures", []) if isinstance(item, dict)}
    dimensions = set(plan.get("dimensions", []))
    return ResultContract(
        resolved_question=question,
        query_plan=plan,
        columns=[ResultColumn(name=column, semantic_role="metric" if column in measures else "dimension" if column in dimensions else "unknown") for column in execution.columns],
        rows=execution.rows,
        row_count=execution.row_count,
        # 业务上 0 值聚合仍有一行结果，只有成功且零行才是空结果。
        result_state="empty" if execution.status == "success" and execution.row_count == 0 else execution.status,
        time_range=str(plan.get("time_filter") or ""),
        warnings=warnings,
    )


def build_visualization_spec(contract: ResultContract) -> VisualizationSpec:
    """只用已确认的执行结果和列角色选择展示形态，模型不能注入图表配置。"""
    if contract.result_state != "success" or contract.row_count < 2:
        return VisualizationSpec(reason="结果行不足或查询未成功，不展示图表")
    columns = [column.name for column in contract.columns]
    dimension = next((column.name for column in contract.columns if column.semantic_role == "dimension"), None)
    dimension = dimension or _first_dimension(columns, contract.rows)
    numeric = _numeric_columns(columns, contract.rows)
    if not dimension or not numeric:
        return VisualizationSpec(reason="缺少可识别的维度列或数值列，不展示图表")
    unit = _unit_for(numeric[0])
    fields = [dimension, *numeric[:2]]
    labels = {field: _field_label(field) for field in fields}
    units = {field: _unit_for(field) for field in numeric[:2]}
    lowered = dimension.lower()
    if "date" in lowered or "month" in lowered:
        measure_labels = "、".join(labels[field] for field in numeric[:2])
        return VisualizationSpec(
            kind="line", title=f"{measure_labels}趋势", x_field=dimension, y_fields=numeric[:2], unit=unit,
            field_labels=labels, field_units=units, reason="时间维度使用趋势图",
        )
    if contract.row_count <= 8 and len(numeric) == 1 and unit != "percent" and any(token in lowered for token in ("status", "method", "source", "type")):
        return VisualizationSpec(
            kind="pie", title=f"{labels[numeric[0]]}构成", x_field=dimension, y_fields=numeric[:1], unit=unit,
            field_labels=labels, field_units=units, reason="有限类别的非比例构成使用环形图",
        )
    if contract.row_count <= 30:
        return VisualizationSpec(
            kind="bar", title=f"{labels[numeric[0]]}对比", x_field=dimension, y_fields=numeric[:1], unit=unit,
            field_labels=labels, field_units=units, reason="类别维度使用柱状图",
        )
    return VisualizationSpec(reason="类别过多，保留结果表以便查看完整数据")


def _first_dimension(columns: list[str], rows: list[dict]) -> str | None:
    for column in columns:
        if rows and not _is_number(rows[0].get(column)):
            return column
    return None


def _numeric_columns(columns: list[str], rows: list[dict]) -> list[str]:
    return [column for column in columns if any(row.get(column) is not None for row in rows) and all(_is_number(row.get(column)) for row in rows if row.get(column) is not None)]


def _is_number(value) -> bool:
    if isinstance(value, bool) or value is None:
        return False
    try:
        float(value)
    except (TypeError, ValueError):
        return False
    return True


def _unit_for(column: str) -> str:
    lowered = column.lower()
    if any(token in lowered for token in ("rate", "ratio", "margin", "percent")):
        return "percent"
    if any(token in lowered for token in ("sales", "amount", "price", "revenue", "gmv", "value")):
        return "currency"
    return "number"


def _field_label(field: str) -> str:
    """业务展示只使用审核字段标签；未知字段保守地转为可读文本。"""
    labels = {
        "order_date": "日期",
        "order_month": "月份",
        "month": "月份",
        "daily_sales": "销售额",
        "sales_amount": "销售额",
        "total_amount": "销售额",
        "order_count": "订单数",
        "avg_order_value": "平均客单价",
        "refund_rate": "退款率",
        "success_rate": "支付成功率",
        "failure_rate": "支付失败率",
        "gross_margin": "毛利率",
        "repeat_rate": "复购率",
        "category": "品类",
        "category_label": "品类",
        "product": "商品",
        "product_label": "商品",
        "city": "城市",
        "city_label": "城市",
        "payment_method": "支付方式",
        "payment_method_label": "支付方式",
    }
    return labels.get(field, field.replace("_", " "))
