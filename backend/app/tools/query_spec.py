import re
from datetime import date

from backend.app.schemas.query_spec import QuerySpec


METRIC_LABELS = {
    "sales_amount": "销售额",
    "order_count": "订单数",
    "avg_order_value": "客单价",
    "refund_rate": "退款率",
    "gross_margin": "毛利率",
    "repeat_rate": "复购率",
    "payment_success_rate": "支付成功率",
    "payment_failure_rate": "支付失败率",
    "new_user_count": "新增用户数",
    "ordering_user_count": "下单用户数",
    "user_purchase_count": "用户购买次数",
    "visit_to_order_conversion_rate": "访问到下单转化率",
    "cart_to_payment_conversion_rate": "加购到支付转化率",
    "coupon_redemption_rate": "优惠券核销率",
    "coupon_order_aov_comparison": "优惠券订单客单价对比",
    "source_order_conversion_rate": "流量来源订单转化率",
}

DIMENSION_LABELS = {
    "date": "按天",
    "month": "按月",
    "category": "按品类",
    "product": "按商品",
    "city": "按城市",
    "state": "按州",
    "payment_type": "按支付方式",
    "source": "按流量来源",
    "user": "按用户",
    "coupon": "按优惠券",
}

_METRIC_REQUIREMENTS = {
    "sales_amount": (["orders", "payments"], ["total_amount"]),
    "order_count": (["orders", "payments"], ["order_count"]),
    "avg_order_value": (["orders"], ["avg_order_value"]),
    "refund_rate": (["refunds", "orders"], ["refund_rate"]),
    "gross_margin": (["order_items", "products", "product_costs"], ["gross_margin"]),
    "repeat_rate": (["orders"], ["repeat"]),
    "payment_success_rate": (["payments"], ["success_rate"]),
    "payment_failure_rate": (["payments"], ["failure_rate"]),
    "new_user_count": (["users"], ["new_user_count"]),
    "ordering_user_count": (["orders", "users"], ["ordering_user_count"]),
    "user_purchase_count": (["orders", "users"], ["purchase_count"]),
    "visit_to_order_conversion_rate": (["traffic_events", "orders"], ["conversion_rate"]),
    "cart_to_payment_conversion_rate": (["traffic_events", "payments"], ["conversion_rate"]),
    "coupon_redemption_rate": (["coupons", "coupon_usages"], ["coupon_redemption_rate"]),
    "coupon_order_aov_comparison": (["orders", "coupon_usages"], ["avg_order_value"]),
    "source_order_conversion_rate": (["traffic_events", "orders"], ["conversion_rate"]),
}

_DIMENSION_OUTPUT_TOKENS = {
    "date": "date",
    "month": "month",
    "category": "category",
    "product": "product",
    "city": "city",
    "payment_type": "payment_method",
    "source": "source",
    "user": "user",
    "coupon": "coupon",
}

_DIMENSION_TABLES = {
    "category": ["order_items", "products"],
    "product": ["order_items", "products"],
    "city": ["users"],
    "state": ["users"],
    "payment_type": ["payments"],
    "source": ["traffic_events"],
    "user": ["users"],
    "coupon": ["coupons", "coupon_usages"],
}


def build_query_spec(
    question: str,
    metrics: list[str],
    dimensions: list[str],
    time_range: str,
    *,
    today: date | None = None,
) -> QuerySpec:
    required_table_groups: list[list[str]] = []
    required_metric_tokens: list[str] = []
    required_dimension_tokens: list[str] = []
    for metric in metrics:
        requirement = _METRIC_REQUIREMENTS.get(metric)
        if requirement is None:
            continue
        tables, tokens = requirement
        required_table_groups.append(tables)
        required_metric_tokens.extend(tokens)

    required_dimension_tokens.extend(
        _DIMENSION_OUTPUT_TOKENS[dimension]
        for dimension in dimensions
        if dimension in _DIMENSION_OUTPUT_TOKENS
    )
    required_table_groups.extend(
        _DIMENSION_TABLES[dimension]
        for dimension in dimensions
        if dimension in _DIMENSION_TABLES
    )
    time_start, time_end = _time_bounds(question, today=today)
    return QuerySpec(
        metrics=sorted(set(metrics)),
        dimensions=sorted(set(dimensions)),
        time_range=time_range,
        time_start=time_start.isoformat() if time_start else "",
        time_end=time_end.isoformat() if time_end else "",
        time_filter=_time_filter_template(time_start, time_end),
        granularity=_granularity(dimensions),
        top_n=_top_n(question),
        requires_order_by=_requires_order_by(question),
        required_table_groups=_unique_groups(required_table_groups),
        required_metric_tokens=sorted(set(required_metric_tokens)),
        required_dimension_tokens=sorted(set(required_dimension_tokens)),
        required_output_tokens=sorted(set(required_metric_tokens) | set(required_dimension_tokens)),
        forbidden_sql_patterns=["orders.status = 'paid'"],
    )


def _granularity(dimensions: list[str]) -> str | None:
    if "month" in dimensions:
        return "month"
    if "date" in dimensions:
        return "day"
    return None


def _top_n(question: str) -> int | None:
    match = re.search(r"前\s*(\d+)\s*个?", question)
    if match:
        return int(match.group(1))
    return None


def _requires_order_by(question: str) -> bool:
    return bool(_top_n(question)) or any(token in question for token in ["最高", "最低", "排行", "排名"])


def _unique_groups(groups: list[list[str]]) -> list[list[str]]:
    unique = {tuple(sorted(set(group))) for group in groups if group}
    return [list(group) for group in sorted(unique)]


def _time_bounds(question: str, *, today: date | None = None) -> tuple[date | None, date | None]:
    reference = today or date.today()
    day_match = re.search(r"(20\d{2})\s*年\s*(\d{1,2})\s*月\s*(\d{1,2})\s*[日号]?", question)
    if day_match:
        target = _valid_date(*map(int, day_match.groups()))
        return (target, _next_day(target)) if target else (None, None)
    month_match = re.search(r"(20\d{2})\s*年\s*(\d{1,2})\s*月", question)
    if month_match:
        start = _valid_date(int(month_match.group(1)), int(month_match.group(2)), 1)
        return (start, _next_month(start)) if start else (None, None)
    year_match = re.search(r"(20\d{2})\s*年", question)
    if year_match:
        start = date(int(year_match.group(1)), 1, 1)
        return start, date(start.year + 1, 1, 1)
    if any(token in question for token in ["今天", "当天", "这一天", "一天"]):
        return reference, _next_day(reference)
    if any(token in question for token in ["本月", "这个月", "这一个月", "一个月"]):
        start = reference.replace(day=1)
        return start, _next_month(start)
    return None, None


def _valid_date(year: int, month: int, day: int) -> date | None:
    try:
        return date(year, month, day)
    except ValueError:
        return None


def _next_day(value: date) -> date:
    return date.fromordinal(value.toordinal() + 1)


def _next_month(value: date) -> date:
    return date(value.year + 1, 1, 1) if value.month == 12 else date(value.year, value.month + 1, 1)


def _time_filter_template(start: date | None, end: date | None) -> str:
    if not start or not end:
        return ""
    return f"{{time_field}} >= DATE '{start.isoformat()}' AND {{time_field}} < DATE '{end.isoformat()}'"
