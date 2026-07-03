from pathlib import Path
import sys

from dotenv import load_dotenv


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from backend.app.db.connection import get_connection


TABLES = [
    "users",
    "products",
    "orders",
    "order_items",
    "payments",
    "refunds",
    "reviews",
    "inventory_snapshots",
    "product_costs",
    "schema_metadata",
    "metric_definitions",
]


def main() -> None:
    load_dotenv(ROOT / "backend" / ".env")
    with get_connection() as conn:
        cursor = conn.cursor()
        for table in TABLES:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            print(f"{table}: {count}")


if __name__ == "__main__":
    main()
