from pathlib import Path
import argparse
import sys

from dotenv import load_dotenv


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from backend.app.services.context_refresh_service import ContextRefreshService
from backend.app.services.embedding_sync_service import EmbeddingSyncResult
from backend.app.services.schema_sync_service import SchemaSyncResult


def main() -> None:
    load_dotenv(ROOT / "backend" / ".env")
    parser = argparse.ArgumentParser(description="刷新 schema metadata 和 embedding 检索上下文")
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
        "--skip-embeddings",
        action="store_true",
        help="只同步 schema_metadata，不同步 embedding",
    )
    parser.add_argument(
        "--embedding-target",
        action="append",
        choices=["schema", "metric", "memory"],
        default=None,
        help="指定 embedding 同步目标，可重复传入；默认同步 schema、metric、memory",
    )
    parser.add_argument(
        "--embedding-limit",
        type=int,
        default=None,
        help="限制每个 embedding 目标本次最多同步的记录数",
    )
    parser.add_argument(
        "--embedding-batch-size",
        type=int,
        default=16,
        help="每次 embedding 请求包含的记录数，默认 16",
    )
    parser.add_argument(
        "--embedding-sleep-ms",
        type=int,
        default=0,
        help="embedding 批次请求之间的等待毫秒数，默认 0",
    )
    args = parser.parse_args()

    result = ContextRefreshService().refresh(
        include_tables=args.include_table,
        exclude_tables=args.exclude_table,
        sync_embeddings=not args.skip_embeddings,
        embedding_targets=args.embedding_target,
        embedding_limit=args.embedding_limit,
        embedding_batch_size=args.embedding_batch_size,
        embedding_sleep_ms=args.embedding_sleep_ms,
    )
    _print_schema_result(result.schema_result)
    for embedding_result in result.embedding_results:
        _print_embedding_result(embedding_result)


def _print_schema_result(result: SchemaSyncResult) -> None:
    print(
        "schema_metadata refreshed: "
        f"scanned={result.scanned_columns}, synced={result.synced_columns}, tables={len(result.tables)}"
    )
    for table in result.tables:
        print(f"- {table}")


def _print_embedding_result(result: EmbeddingSyncResult) -> None:
    print(
        f"{result.target} embeddings refreshed: "
        f"scanned={result.scanned}, updated={result.updated}, failed={result.failed}"
    )
    for error in result.errors[:5]:
        print(f"- {error}")
    if len(result.errors) > 5:
        print(f"- ... {len(result.errors) - 5} more errors")


if __name__ == "__main__":
    main()
