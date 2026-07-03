import re
from dataclasses import dataclass


DEFAULT_SALES_TREND_DAYS = 30
MAX_SALES_TREND_DAYS = 365


@dataclass(frozen=True)
class SalesTrendParameters:
    days: int = DEFAULT_SALES_TREND_DAYS
    granularity: str = "day"

    def model_dump(self) -> dict[str, int | str]:
        return {"days": self.days, "granularity": self.granularity}


def parse_sales_trend_parameters(question: str) -> SalesTrendParameters:
    """从中文业务问题中解析销售趋势参数。"""
    days = _parse_days(question)
    return SalesTrendParameters(days=days, granularity="day")


def render_sales_trend_sql(parameters: SalesTrendParameters) -> str:
    """渲染最近 N 个有交易日期的销售趋势 SQL。"""
    days = max(1, min(parameters.days, MAX_SALES_TREND_DAYS))
    return f"""
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
LIMIT {days}
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


def _bounded_days(days: int) -> int:
    return max(1, min(days, MAX_SALES_TREND_DAYS))
