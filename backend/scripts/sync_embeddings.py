from pathlib import Path
import argparse
import sys

from dotenv import load_dotenv


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from backend.app.services.embedding_sync_service import EmbeddingSyncResult, EmbeddingSyncService


def main() -> None:
    load_dotenv(ROOT / "backend" / ".env")
    parser = argparse.ArgumentParser(description="同步 schema_metadata 和 metric_definitions 的 embedding")
    parser.add_argument(
        "--target",
        choices=["all", "schema", "metric"],
        default="all",
        help="同步目标，默认 all",
    )
    args = parser.parse_args()

    service = EmbeddingSyncService()
    if args.target == "schema":
        results = [service.sync_schema_embeddings()]
    elif args.target == "metric":
        results = [service.sync_metric_embeddings()]
    else:
        results = service.sync_all()

    for result in results:
        _print_result(result)


def _print_result(result: EmbeddingSyncResult) -> None:
    print(
        f"{result.target} embeddings synced: "
        f"scanned={result.scanned}, updated={result.updated}, failed={result.failed}"
    )
    for error in result.errors[:5]:
        print(f"- {error}")
    if len(result.errors) > 5:
        print(f"- ... {len(result.errors) - 5} more errors")


if __name__ == "__main__":
    main()
