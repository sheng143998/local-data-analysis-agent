from pathlib import Path
import sys
from uuid import uuid5, NAMESPACE_DNS

from dotenv import load_dotenv


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from backend.app.db.connection import get_connection
from backend.app.services.schema_sync_service import SchemaSyncService


METRICS = [
    {
        "metric_name": "sales_amount",
        "display_name": "销售额",
        "description": "已支付订单 total_amount 汇总",
        "formula": "SUM(orders.total_amount)",
        "required_tables": ["orders", "payments"],
        "required_fields": ["orders.total_amount", "payments.status"],
        "default_filters": '{"payments.status":"paid"}',
        "example_question": "最近 7 天销售额是多少？",
        "owner": "经营分析组",
    },
    {
        "metric_name": "order_count",
        "display_name": "订单数",
        "description": "去重后的有效订单数量",
        "formula": "COUNT(DISTINCT orders.id)",
        "required_tables": ["orders"],
        "required_fields": ["orders.id", "orders.status"],
        "default_filters": "{}",
        "example_question": "本月订单数较上月变化？",
        "owner": "经营分析组",
    },
    {
        "metric_name": "refund_rate",
        "display_name": "退款率",
        "description": "退款订单数占有效订单数比例",
        "formula": "refund_orders / paid_orders",
        "required_tables": ["refunds", "orders"],
        "required_fields": ["refunds.order_id", "orders.status"],
        "default_filters": "{}",
        "example_question": "哪个品类退款率最高？",
        "owner": "风控分析组",
    },
    {
        "metric_name": "avg_order_value",
        "display_name": "客单价",
        "description": "销售额除以订单数",
        "formula": "sales_amount / order_count",
        "required_tables": ["orders"],
        "required_fields": ["orders.total_amount", "orders.id"],
        "default_filters": "{}",
        "example_question": "最近 30 天平均客单价？",
        "owner": "经营分析组",
    },
]


def seed_metrics(cursor) -> None:
    for metric in METRICS:
        cursor.execute(
            """
            INSERT INTO metric_definitions (
              id, metric_name, display_name, description, formula,
              required_tables, required_fields, default_filters,
              example_question, owner, status
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s::jsonb, %s, %s, 'enabled')
            ON CONFLICT (metric_name) DO UPDATE SET
              display_name = EXCLUDED.display_name,
              description = EXCLUDED.description,
              formula = EXCLUDED.formula,
              required_tables = EXCLUDED.required_tables,
              required_fields = EXCLUDED.required_fields,
              default_filters = EXCLUDED.default_filters,
              example_question = EXCLUDED.example_question,
              owner = EXCLUDED.owner,
              updated_at = now()
            """,
            (
                str(uuid5(NAMESPACE_DNS, metric["metric_name"])),
                metric["metric_name"],
                metric["display_name"],
                metric["description"],
                metric["formula"],
                metric["required_tables"],
                metric["required_fields"],
                metric["default_filters"],
                metric["example_question"],
                metric["owner"],
            ),
        )
    print(f"metric_definitions seeded: {len(METRICS)}")


def seed_schema_metadata(cursor) -> None:
    result = SchemaSyncService().sync_public_schema(
        include_tables=[
            "users",
            "products",
            "orders",
            "order_items",
            "payments",
            "refunds",
            "reviews",
            "traffic_events",
            "coupons",
            "coupon_usages",
            "inventory_snapshots",
            "product_costs",
        ]
    )
    print(f"schema_metadata synced from information_schema: {result.synced_columns}")


def main() -> None:
    load_dotenv(ROOT / "backend" / ".env")
    with get_connection() as conn:
        cursor = conn.cursor()
        seed_metrics(cursor)
        seed_schema_metadata(cursor)


if __name__ == "__main__":
    main()
