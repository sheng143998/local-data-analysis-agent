import argparse
from pathlib import Path
from urllib.request import urlopen


ROOT = Path(__file__).resolve().parents[2]
RAW_DIR = ROOT / "backend" / "app" / "data" / "raw" / "olist"
BASE_URL = "https://raw.githubusercontent.com/olist/work-at-olist-data/master/datasets"

FILES = [
    "olist_customers_dataset.csv",
    "olist_orders_dataset.csv",
    "olist_order_items_dataset.csv",
    "olist_order_payments_dataset.csv",
    "olist_order_reviews_dataset.csv",
    "olist_products_dataset.csv",
    "product_category_name_translation.csv",
]


def download_file(file_name: str, limit_check: bool = False) -> None:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    url = f"{BASE_URL}/{file_name}"
    target = RAW_DIR / file_name
    with urlopen(url, timeout=30) as response:
      if limit_check:
          print(f"available: {file_name} status={response.status}")
          return
      target.write_bytes(response.read())
      print(f"downloaded: {target}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit-check", action="store_true", help="只检查远程文件是否可访问，不下载")
    args = parser.parse_args()

    for file_name in FILES:
        download_file(file_name, limit_check=args.limit_check)


if __name__ == "__main__":
    main()
