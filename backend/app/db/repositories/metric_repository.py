from datetime import datetime, timezone
from uuid import UUID

from backend.app.schemas.metrics import MetricCreate, MetricDefinition, MetricUpdate


class MetricRepository:
    """V1 内存仓储。后续替换为 PostgreSQL repository。"""

    def __init__(self) -> None:
        self._items: dict[UUID, MetricDefinition] = {}
        for metric in _seed_metrics():
            self._items[metric.id] = metric

    def list(self) -> list[MetricDefinition]:
        return sorted(self._items.values(), key=lambda item: item.display_name)

    def get(self, metric_id: UUID) -> MetricDefinition | None:
        return self._items.get(metric_id)

    def create(self, payload: MetricCreate) -> MetricDefinition:
        metric = MetricDefinition(**payload.model_dump())
        self._items[metric.id] = metric
        return metric

    def update(self, metric_id: UUID, payload: MetricUpdate) -> MetricDefinition | None:
        metric = self._items.get(metric_id)
        if metric is None:
            return None

        data = metric.model_dump()
        for key, value in payload.model_dump(exclude_unset=True).items():
            data[key] = value
        data["updated_at"] = datetime.now(timezone.utc)
        updated = MetricDefinition(**data)
        self._items[metric_id] = updated
        return updated

    def delete(self, metric_id: UUID) -> bool:
        return self._items.pop(metric_id, None) is not None


def _seed_metrics() -> list[MetricDefinition]:
    return [
        MetricDefinition(
            metric_name="sales_amount",
            display_name="销售额",
            description="已支付订单 total_amount 汇总",
            formula="SUM(orders.total_amount)",
            required_tables=["orders", "payments"],
            required_fields=["orders.total_amount", "payments.status"],
            default_filters={"payments.status": "paid"},
            example_question="最近 7 天销售额是多少？",
            owner="经营分析组",
        ),
        MetricDefinition(
            metric_name="order_count",
            display_name="订单数",
            description="去重后的有效订单数量",
            formula="COUNT(DISTINCT orders.id)",
            required_tables=["orders"],
            required_fields=["orders.id", "orders.status"],
            example_question="本月订单数较上月变化？",
            owner="经营分析组",
        ),
        MetricDefinition(
            metric_name="refund_rate",
            display_name="退款率",
            description="退款订单数占有效订单数比例",
            formula="refund_orders / paid_orders",
            required_tables=["refunds", "orders"],
            required_fields=["refunds.order_id", "orders.status"],
            example_question="哪个品类退款率最高？",
            owner="风控分析组",
        ),
    ]
