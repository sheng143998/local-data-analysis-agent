from backend.app.db.connection import get_connection
from backend.app.schemas.retrieval import MetricContext
from backend.app.tools.retrieval_scoring import (
    build_search_document,
    keyword_hit_score,
    normalize_search_text,
    text_similarity,
    weighted_score,
)
from backend.app.tools.vector_retrieval import retrieve_metric_vector_candidates


METRIC_KEYWORDS = {
    "sales_amount": {"销售额", "销售", "成交", "gmv", "收入", "金额"},
    "order_count": {"订单", "订单数", "下单", "交易数"},
    "refund_rate": {"退款", "退款率", "退货", "售后"},
    "avg_order_value": {"客单价", "平均订单", "平均金额"},
    "repeat_purchase_rate": {"复购率", "复购", "回购", "重复购买", "repeat"},
    "payment_success_rate": {"支付成功率", "支付成功", "成功率", "success"},
    "payment_failure_rate": {"支付失败率", "支付失败", "失败率", "failure"},
    "category_gross_margin": {"品类毛利", "毛利率", "毛利", "利润率", "gross margin"},
}


def retrieve_metrics(question: str, limit: int = 4) -> list[MetricContext]:
    """从 metric_definitions 召回与问题相关的业务指标。"""
    metrics = _load_enabled_metrics()
    semantic_scores = retrieve_metric_vector_candidates(question, limit=max(limit * 2, 8))
    ranked = sorted(
        (
            _score_metric(
                metric,
                question,
                semantic_score=semantic_scores.get(metric.metric_name, 0),
            )
            for metric in metrics
        ),
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
                semantic_score=0,
                score=0,
            )
            for row in cursor.fetchall()
        ]


def _score_metric(metric: MetricContext, question: str, *, semantic_score: float = 0) -> MetricContext:
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
            "semantic_score": (semantic_score, 0.8),
            "text_similarity": (similarity, 0.4),
            "trend_intent": (trend_intent, 0.2),
        }
    )
    return metric.model_copy(update={"semantic_score": semantic_score, "score": score})
