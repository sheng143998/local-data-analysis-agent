from pathlib import Path
import argparse
import sys

from dotenv import load_dotenv


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from backend.app.services.schema_sync_service import SchemaSyncService


def main() -> None:
    load_dotenv(ROOT / "backend" / ".env")
    parser = argparse.ArgumentParser(description="同步 PostgreSQL public schema 到 schema_metadata")
    parser.add_argument(
        "--include-table",
        action="append",
        default=None,
        help="只同步指定业务表，可重复传入",
    )
    parser.add_argument(
        "--exclude-table",
        action="append",
        default=None,
        help="额外排除指定表，可重复传入",
    )
    parser.add_argument(
        "--refresh-generated-descriptions",
        action="store_true",
        help="刷新早期系统生成的泛化字段说明，保留人工说明",
    )
    args = parser.parse_args()

    result = SchemaSyncService().sync_public_schema(
        include_tables=args.include_table,
        exclude_tables=args.exclude_table,
        refresh_generated_descriptions=args.refresh_generated_descriptions,
    )
    print(
        "schema_metadata synced: "
        f"{result.synced_columns} columns across {len(result.tables)} tables"
    )
    for table in result.tables:
        print(f"- {table}")


if __name__ == "__main__":
    main()
