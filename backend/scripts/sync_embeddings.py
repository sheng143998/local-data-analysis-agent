from pathlib import Path
import argparse
import sys

from dotenv import load_dotenv


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from backend.app.services.embedding_sync_service import EmbeddingSyncResult, EmbeddingSyncService


def main() -> None:
    load_dotenv(ROOT / "backend" / ".env")
    parser = argparse.ArgumentParser(description="同步 schema、metric 和 SQL Memory 的 embedding")
    parser.add_argument(
        "--target",
        choices=["all", "schema", "metric", "memory"],
        default="all",
        help="同步目标，默认 all",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="限制每个目标本次最多同步的记录数",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=16,
        help="每次 embedding 请求包含的记录数，默认 16",
    )
    args = parser.parse_args()

    service = EmbeddingSyncService()
    if args.target == "schema":
        results = [service.sync_schema_embeddings(limit=args.limit, batch_size=args.batch_size)]
    elif args.target == "metric":
        results = [service.sync_metric_embeddings(limit=args.limit, batch_size=args.batch_size)]
    elif args.target == "memory":
        results = [service.sync_sql_memory_embeddings(limit=args.limit, batch_size=args.batch_size)]
    else:
        results = service.sync_all(limit=args.limit, batch_size=args.batch_size)

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
