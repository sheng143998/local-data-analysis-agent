from pathlib import Path
import sys

from dotenv import load_dotenv


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from backend.app.services.schema_sync_service import SchemaSyncService


def main() -> None:
    load_dotenv(ROOT / "backend" / ".env")
    result = SchemaSyncService().sync_public_schema()
    print(
        "schema_metadata synced: "
        f"{result.synced_columns} columns across {len(result.tables)} tables"
    )
    for table in result.tables:
        print(f"- {table}")


if __name__ == "__main__":
    main()
