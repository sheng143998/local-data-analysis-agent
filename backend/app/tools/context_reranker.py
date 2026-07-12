from __future__ import annotations

from dataclasses import dataclass, field

from backend.app.schemas.retrieval import MetricContext, SchemaColumnContext
from backend.app.tools.retrieval_scoring import (
    keyword_hit_score,
    normalize_search_text,
    weighted_score,
)


MAX_SCHEMA_COLUMNS = 80

METRIC_INTENT_KEYWORDS: dict[str, set[str]] = {
    "sales_amount": {"sales", "sale", "gmv", "revenue", "amount", "销售额", "销售", "收入", "成交额"},
    "order_count": {"order", "orders", "count", "订单", "订单数", "下单"},
    "refund_rate": {"refund", "refunds", "return", "退款", "退款率", "售后"},
    "avg_order_value": {"aov", "avg", "average", "客单价", "平均订单", "平均金额"},
    "repeat_purchase_rate": {"repeat", "repurchase", "复购", "回购", "复购率"},
    "payment_success_rate": {"payment", "success", "paid", "支付", "支付成功", "成功率"},
    "payment_failure_rate": {"payment", "failure", "failed", "支付失败", "失败率"},
    "category_gross_margin": {"margin", "gross", "profit", "毛利", "毛利率", "利润率"},
}

TABLE_INTENT_KEYWORDS: dict[str, set[str]] = {
    "orders": {"order", "orders", "订单", "下单", "成交"},
    "payments": {"payment", "paid", "pay", "支付", "付款"},
    "refunds": {"refund", "return", "退款", "售后"},
    "order_items": {"item", "items", "sku", "商品", "产品", "明细"},
    "products": {"product", "products", "sku", "category", "商品", "产品", "品类", "类目"},
    "product_costs": {"cost", "margin", "成本", "毛利", "利润"},
    "users": {"user", "customer", "buyer", "city", "用户", "客户", "买家", "城市", "地区"},
    "traffic_events": {"traffic", "visit", "source", "conversion", "流量", "访问", "访客", "来源", "转化"},
    "coupons": {"coupon", "discount", "优惠券", "券", "折扣"},
    "coupon_usages": {"coupon", "usage", "redeem", "核销", "用券", "领券"},
}

FIELD_INTENT_KEYWORDS: dict[str, set[str]] = {
    "category": {"category", "品类", "类目", "分类"},
    "city": {"city", "城市", "地区", "地域"},
    "payment_type": {"payment_method", "payment type", "method", "支付方式", "付款方式"},
    "product_id": {"product", "sku", "商品", "产品"},
    "user_id": {"user", "customer", "用户", "客户", "买家"},
    "status": {"status", "state", "状态", "成功", "失败", "已支付"},
}

TIME_KEYWORDS = {
    "date",
    "day",
    "daily",
    "month",
    "monthly",
    "trend",
    "recent",
    "last",
    "时间",
    "日期",
    "每天",
    "按天",
    "每日",
    "每月",
    "按月",
    "趋势",
    "最近",
    "过去",
}
TIME_FIELD_NAMES = {"created_at", "updated_at", "paid_at", "refunded_at", "event_time", "date", "month"}
JOIN_FIELD_SUFFIXES = ("_id",)


@dataclass
class ContextRerankDiagnostics:
    intents: dict[str, list[str] | bool] = field(default_factory=dict)
    metric_scores: list[dict[str, float | str]] = field(default_factory=list)
    schema_scores: list[dict[str, float | str]] = field(default_factory=list)
    compression: dict[str, int] = field(default_factory=dict)
    coverage: dict[str, list[str]] = field(default_factory=dict)

    def summary_lines(self, *, metric_limit: int = 4, schema_limit: int = 8) -> list[str]:
        metric_parts = [
            f"{item['name']}={float(item['score']):.2f}"
            for item in self.metric_scores[:metric_limit]
        ]
        schema_parts = [
            f"{item['field']}={float(item['score']):.2f}"
            for item in self.schema_scores[:schema_limit]
        ]
        compression = self.compression
        lines = [
            "Rerank diagnostics: "
            f"intents={self.intents}; "
            f"metrics=[{', '.join(metric_parts)}]; "
            f"fields=[{', '.join(schema_parts)}]; "
            f"schema_columns={compression.get('kept', 0)}/{compression.get('input', 0)}",
        ]
        missing = self.coverage.get("missing_required_fields", [])
        if missing:
            lines.append("Rerank warning: missing required fields after compression: " + ", ".join(missing))
        return lines

    def as_dict(self) -> dict:
        return {
            "intents": self.intents,
            "metric_scores": self.metric_scores,
            "schema_scores": self.schema_scores,
            "compression": self.compression,
            "coverage": self.coverage,
            "summary": self.summary_lines(),
        }


def rerank_context(
    question: str,
    metrics: list[MetricContext],
    schema_columns: list[SchemaColumnContext],
    *,
    max_schema_columns: int = MAX_SCHEMA_COLUMNS,
) -> tuple[list[MetricContext], list[SchemaColumnContext], ContextRerankDiagnostics]:
    intents = detect_retrieval_intents(question, metrics)
    reranked_metrics = _rerank_metrics(question, metrics, intents)
    required_fields = _required_metric_fields(reranked_metrics)
    reranked_schema = _rerank_schema(question, schema_columns, intents, required_fields)
    compressed_schema = _compress_schema(reranked_schema, required_fields, max_schema_columns)
    diagnostics = ContextRerankDiagnostics(
        intents={
            "metric": sorted(intents.metric_names),
            "table": sorted(intents.tables),
            "field": sorted(intents.fields),
            "time": intents.time,
        },
        metric_scores=[
            {"name": metric.metric_name, "score": metric.score, "semantic": metric.semantic_score}
            for metric in reranked_metrics
        ],
        schema_scores=[
            {
                "field": f"{column.table_name}.{column.column_name}",
                "score": column.score,
                "semantic": column.semantic_score,
            }
            for column in compressed_schema
        ],
        compression={"input": len(schema_columns), "kept": len(compressed_schema), "max": max_schema_columns},
        coverage={
            "required_fields": sorted(required_fields),
            "missing_required_fields": sorted(
                required_fields
                - {f"{column.table_name}.{column.column_name}" for column in compressed_schema}
            ),
        },
    )
    return reranked_metrics, compressed_schema, diagnostics


@dataclass(frozen=True)
class RetrievalIntents:
    metric_names: set[str]
    tables: set[str]
    fields: set[str]
    time: bool


def detect_retrieval_intents(question: str, metrics: list[MetricContext] | None = None) -> RetrievalIntents:
    normalized_question = normalize_search_text(question)
    metric_names = _matching_keys(normalized_question, METRIC_INTENT_KEYWORDS)
    table_names = _matching_keys(normalized_question, TABLE_INTENT_KEYWORDS)
    field_names = _matching_keys(normalized_question, FIELD_INTENT_KEYWORDS)
    has_time = keyword_hit_score(normalized_question, TIME_KEYWORDS) > 0

    for metric in metrics or []:
        if metric.metric_name in metric_names:
            table_names.update(metric.required_tables)
            field_names.update(field.rsplit(".", 1)[-1] for field in metric.required_fields)

    return RetrievalIntents(
        metric_names=metric_names,
        tables=table_names,
        fields=field_names,
        time=has_time,
    )


def _rerank_metrics(
    question: str,
    metrics: list[MetricContext],
    intents: RetrievalIntents,
) -> list[MetricContext]:
    ranked: list[MetricContext] = []
    for metric in metrics:
        intent_match = 1.0 if metric.metric_name in intents.metric_names else 0.0
        table_match = _overlap_ratio(metric.required_tables, intents.tables)
        field_match = _overlap_ratio(
            [field.rsplit(".", 1)[-1] for field in metric.required_fields],
            intents.fields,
        )
        time_match = 1.0 if intents.time and _metric_supports_time(metric) else 0.0
        base_score = _normalize_existing_score(metric.score, max_score=3.4)
        rerank_score = weighted_score(
            {
                "base_score": (base_score, 0.55),
                "semantic_score": (metric.semantic_score, 0.15),
                "metric_intent": (intent_match, 0.20),
                "table_intent": (table_match, 0.05),
                "field_intent": (field_match, 0.03),
                "time_intent": (time_match, 0.02),
            }
        )
        ranked.append(metric.model_copy(update={"score": rerank_score}))
    return sorted(ranked, key=lambda item: (-item.score, -item.semantic_score, item.display_name))


def _rerank_schema(
    question: str,
    schema_columns: list[SchemaColumnContext],
    intents: RetrievalIntents,
    required_fields: set[str],
) -> list[SchemaColumnContext]:
    ranked: list[SchemaColumnContext] = []
    for column in schema_columns:
        field_name = f"{column.table_name}.{column.column_name}"
        required_match = 1.0 if field_name in required_fields else 0.0
        table_match = 1.0 if column.table_name in intents.tables else 0.0
        field_match = 1.0 if column.column_name in intents.fields else 0.0
        time_match = 1.0 if intents.time and _is_time_column(column) else 0.0
        join_key = 1.0 if _is_join_column(column.column_name) else 0.0
        lexical_match = keyword_hit_score(
            question,
            {
                column.table_name,
                column.column_name,
                field_name,
                column.description,
                column.business_meaning,
            },
        )
        base_score = _normalize_existing_score(column.score, max_score=3.2)
        rerank_score = weighted_score(
            {
                "base_score": (base_score, 0.40),
                "required_field": (required_match, 0.22),
                "table_intent": (table_match, 0.10),
                "field_intent": (field_match, 0.10),
                "time_intent": (time_match, 0.08),
                "semantic_score": (column.semantic_score, 0.05),
                "lexical_match": (lexical_match, 0.03),
                "join_key": (join_key, 0.02),
            }
        )
        ranked.append(column.model_copy(update={"score": rerank_score}))
    return sorted(
        ranked,
        key=lambda item: (
            -item.score,
            f"{item.table_name}.{item.column_name}" not in required_fields,
            item.table_name,
            item.column_name,
        ),
    )


def _compress_schema(
    schema_columns: list[SchemaColumnContext],
    required_fields: set[str],
    max_schema_columns: int,
) -> list[SchemaColumnContext]:
    if max_schema_columns <= 0 or len(schema_columns) <= max_schema_columns:
        return schema_columns

    selected: list[SchemaColumnContext] = []
    seen: set[str] = set()

    def add(column: SchemaColumnContext) -> None:
        field_name = f"{column.table_name}.{column.column_name}"
        if field_name in seen or len(selected) >= max_schema_columns:
            return
        seen.add(field_name)
        selected.append(column)

    for column in schema_columns:
        if f"{column.table_name}.{column.column_name}" in required_fields:
            add(column)
    for column in schema_columns:
        if _is_time_column(column) or _is_join_column(column.column_name):
            add(column)
    for column in schema_columns:
        add(column)

    return selected


def _matching_keys(normalized_question: str, keyword_map: dict[str, set[str]]) -> set[str]:
    return {
        key
        for key, keywords in keyword_map.items()
        if keyword_hit_score(normalized_question, keywords) > 0
    }


def _required_metric_fields(metrics: list[MetricContext]) -> set[str]:
    return {
        field
        for metric in metrics
        for field in metric.required_fields
        if "." in field
    }


def _metric_supports_time(metric: MetricContext) -> bool:
    return any(field.rsplit(".", 1)[-1] in TIME_FIELD_NAMES for field in metric.required_fields)


def _is_time_column(column: SchemaColumnContext) -> bool:
    return column.column_name in TIME_FIELD_NAMES or column.data_type.lower() in {"date", "timestamp", "timestamptz"}


def _is_join_column(column_name: str) -> bool:
    return column_name == "id" or column_name.endswith(JOIN_FIELD_SUFFIXES)


def _overlap_ratio(left: list[str], right: set[str]) -> float:
    left_values = {normalize_search_text(value) for value in left if value}
    right_values = {normalize_search_text(value) for value in right if value}
    if not left_values or not right_values:
        return 0.0
    return round(len(left_values & right_values) / len(left_values), 4)


def _normalize_existing_score(score: float, *, max_score: float) -> float:
    if max_score <= 0:
        return 0.0
    return round(max(0.0, min(float(score) / max_score, 1.0)), 4)
