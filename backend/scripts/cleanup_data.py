"""数据生命周期清理（计划 4a）：过期会话、失效登录态与老旧运行日志。

用法：py -3 backend/scripts/cleanup_data.py [--runs-retention-days 90] [--dry-run]
建议配合 Windows 任务计划程序每日执行一次。
"""
from argparse import ArgumentParser
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from backend.app.db.connection import get_connection  # noqa: E402


STATEMENTS = [
    ("过期会话状态", "DELETE FROM conversation_states WHERE expires_at IS NOT NULL AND expires_at < now()"),
    ("已撤销/过期登录会话", "DELETE FROM auth_sessions WHERE revoked_at IS NOT NULL OR absolute_expires_at < now()"),
    ("老旧工具调用日志", "DELETE FROM tool_calls WHERE created_at < now() - (%s || ' days')::interval"),
    ("老旧运行记录", "DELETE FROM query_runs WHERE created_at < now() - (%s || ' days')::interval"),
]


def main() -> None:
    parser = ArgumentParser(description="清理过期数据")
    parser.add_argument("--runs-retention-days", type=int, default=90)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    with get_connection() as conn:
        cursor = conn.cursor()
        for label, statement in STATEMENTS:
            params = (str(args.runs_retention_days),) if "%s" in statement else ()
            if args.dry_run:
                count_sql = statement.replace("DELETE FROM", "SELECT COUNT(*) FROM", 1)
                cursor.execute(count_sql, params)
                print(f"[dry-run] {label}: {cursor.fetchone()[0]} 行将被清理")
            else:
                cursor.execute(statement, params)
                print(f"{label}: 已清理 {cursor.rowcount} 行")


if __name__ == "__main__":
    main()
