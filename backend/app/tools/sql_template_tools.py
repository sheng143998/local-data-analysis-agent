import re
from dataclasses import dataclass
from typing import Literal


DEFAULT_SALES_TREND_DAYS = 30
MAX_SALES_TREND_DAYS = 365
Granularity = Literal["day", "month"]
MetricIntent = Literal[
    "sales_amount",
    "order_count",
    "top_product_sales",
    "top_category_sales",
    "category_refund_rate",
    "payment_success_rate",
    "payment_failure_rate",
]


@dataclass(frozen=True)
class SalesTrendParameters:
    days: int = DEFAULT_SALES_TREND_DAYS
    granularity: Granularity = "day"
    metric: MetricIntent = "sales_amount"
    limit: int = 30

    def model_dump(self) -> dict[str, int | str]:
        return {
            "days": self.days,
            "granularity": self.granularity,
            "metric": self.metric,
            "limit": self.limit,
        }


def parse_sales_trend_parameters(question: str) -> SalesTrendParameters:
    """从中文业务问题中解析销售趋势参数。"""
    days = _parse_days(question)
    return SalesTrendParameters(
        days=days,
        granularity=_parse_granularity(question),
        metric=_parse_metric(question),
        limit=_parse_limit(question),
    )


def render_sales_trend_sql(parameters: SalesTrendParameters) -> str:
    """渲染最近 N 个业务时间桶的销售/订单趋势 SQL。"""
    if parameters.metric == "top_product_sales":
        return _render_top_product_sales_sql(parameters)
    if parameters.metric == "top_category_sales":
        return _render_top_category_sales_sql(parameters)
    if parameters.metric == "category_refund_rate":
        return _render_category_refund_rate_sql(parameters)
    if parameters.metric == "payment_success_rate":
        return _render_payment_success_rate_sql(success=True)
    if parameters.metric == "payment_failure_rate":
        return _render_payment_success_rate_sql(success=False)

    days = max(1, min(parameters.days, MAX_SALES_TREND_DAYS))
    time_bucket = _time_bucket_expression(parameters.granularity)
    limit = _bucket_limit(days, parameters.granularity)
    return f"""
SELECT
  {time_bucket} AS order_date,
  SUM(o.total_amount) AS daily_sales,
  COUNT(DISTINCT o.id) AS order_count,
  ROUND(SUM(o.total_amount) / NULLIF(COUNT(DISTINCT o.id), 0), 2) AS avg_order_value,
  ROUND(COUNT(DISTINCT r.id)::numeric / NULLIF(COUNT(DISTINCT o.id), 0) * 100, 2) AS refund_rate
FROM orders o
LEFT JOIN payments p ON p.order_id = o.id
LEFT JOIN refunds r ON r.order_id = o.id
WHERE o.created_at IS NOT NULL
  AND p.status = 'paid'
GROUP BY {time_bucket}
ORDER BY order_date DESC
LIMIT {limit}
"""


def _parse_days(question: str) -> int:
    match = re.search(r"最近\s*(\d+)\s*(天|日)", question)
    if match:
        return _bounded_days(int(match.group(1)))

    if "最近一周" in question or "近一周" in question:
        return 7
    if "最近一个月" in question or "近一个月" in question:
        return 30
    if "最近三个月" in question or "近三个月" in question:
        return 90
    return DEFAULT_SALES_TREND_DAYS


def _parse_granularity(question: str) -> Granularity:
    if any(keyword in question for keyword in ["每月", "按月", "月度", "分月"]):
        return "month"
    return "day"


def _parse_metric(question: str) -> MetricIntent:
    if any(keyword in question for keyword in ["支付失败率", "失败率"]):
        return "payment_failure_rate"
    if any(keyword in question for keyword in ["支付成功率", "成功率", "支付方式"]):
        return "payment_success_rate"
    if any(keyword in question for keyword in ["退款率", "退款", "售后"]):
        return "category_refund_rate"
    if any(keyword in question for keyword in ["品类", "类目", "分类"]):
        return "top_category_sales"
    if any(keyword in question for keyword in ["商品", "产品", "sku", "SKU"]):
        return "top_product_sales"
    if any(keyword in question for keyword in ["订单数", "订单量", "下单数", "下单量"]):
        return "order_count"
    return "sales_amount"


def _parse_limit(question: str) -> int:
    match = re.search(r"(前|top)\s*(\d+)", question, flags=re.IGNORECASE)
    if match:
        return max(1, min(int(match.group(2)), 50))
    return 10 if any(keyword in question for keyword in ["最高", "排行", "排名", "top", "Top"]) else 30


def _bounded_days(days: int) -> int:
    return max(1, min(days, MAX_SALES_TREND_DAYS))


def _time_bucket_expression(granularity: Granularity) -> str:
    if granularity == "month":
        return "DATE_TRUNC('month', o.created_at)::date"
    return "DATE(o.created_at)"


def _bucket_limit(days: int, granularity: Granularity) -> int:
    if granularity == "month":
        return max(1, min(12, (days + 29) // 30))
    return days


def _render_top_product_sales_sql(parameters: SalesTrendParameters) -> str:
    limit = max(1, min(parameters.limit, 50))
    return f"""
SELECT
  COALESCE(oi.product_id, '未知商品') AS product_label,
  COALESCE(p.category, '未分类') AS product_category,
  SUM(oi.price) AS daily_sales,
  COUNT(DISTINCT o.id) AS order_count,
  ROUND(SUM(oi.price) / NULLIF(COUNT(DISTINCT o.id), 0), 2) AS avg_order_value,
  ROUND(COUNT(DISTINCT r.id)::numeric / NULLIF(COUNT(DISTINCT o.id), 0) * 100, 2) AS refund_rate
FROM order_items oi
JOIN orders o ON o.id = oi.order_id
LEFT JOIN products p ON p.id = oi.product_id
LEFT JOIN payments pay ON pay.order_id = o.id
LEFT JOIN refunds r ON r.order_id = o.id
WHERE pay.status = 'paid'
GROUP BY COALESCE(oi.product_id, '未知商品'), COALESCE(p.category, '未分类')
ORDER BY daily_sales DESC
LIMIT {limit}
"""


def _render_top_category_sales_sql(parameters: SalesTrendParameters) -> str:
    limit = max(1, min(parameters.limit, 50))
    return f"""
SELECT
  COALESCE(p.category, '未分类') AS category_label,
  SUM(oi.price) AS daily_sales,
  COUNT(DISTINCT o.id) AS order_count,
  ROUND(SUM(oi.price) / NULLIF(COUNT(DISTINCT o.id), 0), 2) AS avg_order_value,
  ROUND(COUNT(DISTINCT r.id)::numeric / NULLIF(COUNT(DISTINCT o.id), 0) * 100, 2) AS refund_rate
FROM order_items oi
JOIN orders o ON o.id = oi.order_id
LEFT JOIN products p ON p.id = oi.product_id
LEFT JOIN payments pay ON pay.order_id = o.id
LEFT JOIN refunds r ON r.order_id = o.id
WHERE pay.status = 'paid'
GROUP BY COALESCE(p.category, '未分类')
ORDER BY daily_sales DESC
LIMIT {limit}
"""


def _render_category_refund_rate_sql(parameters: SalesTrendParameters) -> str:
    limit = max(1, min(parameters.limit, 50))
    return f"""
SELECT
  COALESCE(p.category, '未分类') AS category_label,
  SUM(oi.price) AS daily_sales,
  COUNT(DISTINCT o.id) AS order_count,
  ROUND(SUM(oi.price) / NULLIF(COUNT(DISTINCT o.id), 0), 2) AS avg_order_value,
  ROUND(COUNT(DISTINCT r.id)::numeric / NULLIF(COUNT(DISTINCT o.id), 0) * 100, 2) AS refund_rate
FROM order_items oi
JOIN orders o ON o.id = oi.order_id
LEFT JOIN products p ON p.id = oi.product_id
LEFT JOIN payments pay ON pay.order_id = o.id
LEFT JOIN refunds r ON r.order_id = o.id
WHERE pay.status = 'paid'
GROUP BY COALESCE(p.category, '未分类')
HAVING COUNT(DISTINCT o.id) > 0
ORDER BY refund_rate DESC, daily_sales DESC
LIMIT {limit}
"""


def _render_payment_success_rate_sql(*, success: bool) -> str:
    rate_alias = "success_rate" if success else "failure_rate"
    rate_condition = "pay.status = 'paid'" if success else "pay.status <> 'paid'"
    return f"""
SELECT
  COALESCE(pay.payment_type, '未知支付方式') AS payment_method_label,
  SUM(pay.amount) AS daily_sales,
  COUNT(DISTINCT pay.order_id) AS order_count,
  ROUND(SUM(pay.amount) / NULLIF(COUNT(DISTINCT pay.order_id), 0), 2) AS avg_order_value,
  ROUND(COUNT(DISTINCT CASE WHEN {rate_condition} THEN pay.order_id END)::numeric / NULLIF(COUNT(DISTINCT pay.order_id), 0) * 100, 2) AS {rate_alias}
FROM payments pay
GROUP BY COALESCE(pay.payment_type, '未知支付方式')
HAVING COUNT(DISTINCT pay.order_id) > 0
ORDER BY {rate_alias} DESC, order_count DESC
LIMIT 20
"""
