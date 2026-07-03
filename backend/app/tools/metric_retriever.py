from backend.app.db.connection import get_connection
from backend.app.schemas.retrieval import MetricContext


METRIC_KEYWORDS = {
    "sales_amount": {"销售额", "销售", "成交", "gmv", "收入", "金额"},
    "order_count": {"订单", "订单数", "下单", "交易数"},
    "refund_rate": {"退款", "退款率", "退货", "售后"},
    "avg_order_value": {"客单价", "平均订单", "平均金额"},
}


def retrieve_metrics(question: str, limit: int = 4) -> list[MetricContext]:
    """从 metric_definitions 召回与问题相关的业务指标。"""
    metrics = _load_enabled_metrics()
    ranked = sorted(
        (_score_metric(metric, question) for metric in metrics),
        key=lambda item: (-item.score, item.display_name),
    )
    return [metric for metric in ranked if metric.score > 0][:limit]


def _load_enabled_metrics() -> list[MetricContext]:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT metric_name, display_name, description, formula,
                   required_tables, required_fields
            FROM metric_definitions
            WHERE status = 'enabled'
            ORDER BY display_name
            """
        )
        return [
            MetricContext(
                metric_name=row[0],
                display_name=row[1],
                description=row[2],
                formula=row[3],
                required_tables=list(row[4] or []),
                required_fields=list(row[5] or []),
                score=0,
            )
            for row in cursor.fetchall()
        ]


def _score_metric(metric: MetricContext, question: str) -> MetricContext:
    lowered = question.lower()
    text = " ".join(
        [
            metric.metric_name,
            metric.display_name,
            metric.description,
            metric.formula,
            " ".join(metric.required_tables),
            " ".join(metric.required_fields),
        ]
    ).lower()

    score = 0.0
    if metric.display_name and metric.display_name in question:
        score += 1.0
    if metric.metric_name.lower() in lowered:
        score += 1.0
    for keyword in METRIC_KEYWORDS.get(metric.metric_name, set()):
        keyword_lower = keyword.lower()
        if keyword_lower in lowered:
            score += 0.8
        elif keyword_lower in text and keyword_lower in lowered:
            score += 0.4
    if any(token in question for token in ["趋势", "按天", "每天", "最近"]):
        if metric.metric_name in {"sales_amount", "order_count", "avg_order_value", "refund_rate"}:
            score += 0.2

    return metric.model_copy(update={"score": round(score, 4)})
