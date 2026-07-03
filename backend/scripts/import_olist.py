import csv
from pathlib import Path
import sys
from typing import Iterable

from dotenv import load_dotenv


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from backend.app.db.connection import get_connection

RAW_DIR = ROOT / "backend" / "app" / "data" / "raw" / "olist"


def read_csv(file_name: str) -> Iterable[dict[str, str]]:
    path = RAW_DIR / file_name
    if not path.exists():
        raise FileNotFoundError(f"缺少数据文件：{path}，请先运行 py -3 backend/scripts/download_olist.py")
    with path.open("r", encoding="utf-8") as file:
        yield from csv.DictReader(file)


def none_if_empty(value: str | None) -> str | None:
    return value or None


def import_users(cursor) -> None:
    rows = [
        (
            row["customer_id"],
            row["customer_unique_id"],
            row["customer_zip_code_prefix"],
            row["customer_city"],
            row["customer_state"],
        )
        for row in read_csv("olist_customers_dataset.csv")
    ]
    cursor.executemany(
        """
        INSERT INTO users (id, unique_id, zip_code_prefix, city, state)
        VALUES (%s, %s, %s, %s, %s)
        ON CONFLICT (id) DO NOTHING
        """,
        rows,
    )
    print(f"users imported: {len(rows)}")


def import_products(cursor) -> None:
    rows = [
        (
            row["product_id"],
            none_if_empty(row.get("product_category_name")),
            none_if_empty(row.get("product_name_lenght")),
            none_if_empty(row.get("product_description_lenght")),
            none_if_empty(row.get("product_photos_qty")),
            none_if_empty(row.get("product_weight_g")),
            none_if_empty(row.get("product_length_cm")),
            none_if_empty(row.get("product_height_cm")),
            none_if_empty(row.get("product_width_cm")),
        )
        for row in read_csv("olist_products_dataset.csv")
    ]
    cursor.executemany(
        """
        INSERT INTO products (
          id, category, name_length, description_length, photos_qty,
          weight_g, length_cm, height_cm, width_cm
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (id) DO NOTHING
        """,
        rows,
    )
    print(f"products imported: {len(rows)}")


def import_orders(cursor) -> None:
    rows = [
        (
            row["order_id"],
            row["customer_id"],
            row["order_status"],
            none_if_empty(row.get("order_purchase_timestamp")),
            none_if_empty(row.get("order_approved_at")),
            none_if_empty(row.get("order_delivered_carrier_date")),
            none_if_empty(row.get("order_delivered_customer_date")),
            none_if_empty(row.get("order_estimated_delivery_date")),
            none_if_empty(row.get("order_purchase_timestamp")),
        )
        for row in read_csv("olist_orders_dataset.csv")
    ]
    cursor.executemany(
        """
        INSERT INTO orders (
          id, user_id, status, purchase_at, approved_at,
          delivered_carrier_at, delivered_customer_at, estimated_delivery_at, created_at
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (id) DO NOTHING
        """,
        rows,
    )
    print(f"orders imported: {len(rows)}")


def import_order_items(cursor) -> None:
    rows = [
        (
            row["order_id"],
            int(row["order_item_id"]),
            row["product_id"],
            row["seller_id"],
            none_if_empty(row.get("shipping_limit_date")),
            row["price"],
            row["freight_value"],
        )
        for row in read_csv("olist_order_items_dataset.csv")
    ]
    cursor.executemany(
        """
        INSERT INTO order_items (
          order_id, item_seq, product_id, seller_id, shipping_limit_at, price, freight_value
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT DO NOTHING
        """,
        rows,
    )
    print(f"order_items imported: {len(rows)}")


def import_payments(cursor) -> None:
    rows = [
        (
            row["order_id"],
            int(row["payment_sequential"]),
            row["payment_type"],
            int(row["payment_installments"]),
            row["payment_value"],
        )
        for row in read_csv("olist_order_payments_dataset.csv")
    ]
    cursor.executemany(
        """
        INSERT INTO payments (
          order_id, payment_sequential, payment_type, installments, amount, status
        )
        VALUES (%s, %s, %s, %s, %s, 'paid')
        ON CONFLICT DO NOTHING
        """,
        rows,
    )
    cursor.execute(
        """
        UPDATE orders o
        SET total_amount = p.total_amount
        FROM (
          SELECT order_id, SUM(amount) AS total_amount
          FROM payments
          GROUP BY order_id
        ) p
        WHERE p.order_id = o.id
        """
    )
    print(f"payments imported: {len(rows)}")


def import_reviews(cursor) -> None:
    rows = [
        (
            row["review_id"],
            row["order_id"],
            none_if_empty(row.get("review_score")),
            none_if_empty(row.get("review_comment_title")),
            none_if_empty(row.get("review_comment_message")),
            none_if_empty(row.get("review_creation_date")),
            none_if_empty(row.get("review_answer_timestamp")),
        )
        for row in read_csv("olist_order_reviews_dataset.csv")
    ]
    cursor.executemany(
        """
        INSERT INTO reviews (
          id, order_id, score, comment_title, comment_message, created_at, answered_at
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (id) DO NOTHING
        """,
        rows,
    )
    print(f"reviews imported: {len(rows)}")


def build_enhanced_tables(cursor) -> None:
    cursor.execute(
        """
        INSERT INTO refunds (order_id, amount, reason, created_at)
        SELECT id, total_amount, status, COALESCE(created_at, now())
        FROM orders
        WHERE status IN ('canceled', 'unavailable')
        ON CONFLICT DO NOTHING
        """
    )
    cursor.execute(
        """
        INSERT INTO product_costs (product_id, unit_cost)
        SELECT id, GREATEST(1, COALESCE(weight_g, 500) * 0.01)
        FROM products
        ON CONFLICT (product_id) DO NOTHING
        """
    )
    cursor.execute(
        """
        INSERT INTO inventory_snapshots (product_id, stock_qty, snapshot_at)
        SELECT id, 50 + (abs(hashtext(id)) % 500), now()
        FROM products
        ON CONFLICT DO NOTHING
        """
    )
    print("enhanced tables built: refunds, product_costs, inventory_snapshots")


def main() -> None:
    load_dotenv(ROOT / "backend" / ".env")
    with get_connection() as conn:
        cursor = conn.cursor()
        import_users(cursor)
        import_products(cursor)
        import_orders(cursor)
        import_order_items(cursor)
        import_payments(cursor)
        import_reviews(cursor)
        build_enhanced_tables(cursor)


if __name__ == "__main__":
    main()
