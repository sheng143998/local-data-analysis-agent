from backend.app.db.connection import get_connection
from backend.app.schemas.retrieval import MetricContext
from backend.app.tools.retrieval_scoring import (
    build_search_document,
    keyword_hit_score,
    normalize_search_text,
    text_similarity,
    weighted_score,
)


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
    normalized_question = normalize_search_text(question)
    document = build_search_document(
        [
            metric.metric_name,
            metric.display_name,
            metric.description,
            metric.formula,
            " ".join(metric.required_tables),
            " ".join(metric.required_fields),
        ]
    )

    display_name = normalize_search_text(metric.display_name)
    metric_name = normalize_search_text(metric.metric_name)
    name_match = 1.0 if (
        (display_name and display_name in normalized_question)
        or (metric_name and metric_name in normalized_question)
    ) else 0.0
    keyword_score = keyword_hit_score(question, METRIC_KEYWORDS.get(metric.metric_name, set()))
    similarity = text_similarity(question, document)
    trend_intent = 1.0 if (
        any(token in question for token in ["趋势", "按天", "每天", "最近"])
        and metric.metric_name in {"sales_amount", "order_count", "avg_order_value", "refund_rate"}
    ) else 0.0

    score = weighted_score(
        {
            "name_match": (name_match, 1.0),
            "keyword_score": (keyword_score, 1.0),
            "text_similarity": (similarity, 0.4),
            "trend_intent": (trend_intent, 0.2),
        }
    )
    return metric.model_copy(update={"score": score})
