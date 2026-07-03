from pathlib import Path
import sys

from dotenv import load_dotenv


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from backend.app.db.connection import get_connection, get_database_url

MIGRATION_DIR = ROOT / "backend" / "app" / "db" / "migrations"


def ensure_database() -> None:
    target_url = get_database_url()
    database_name = target_url.rsplit("/", 1)[-1]
    with get_connection(database="postgres") as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT 1 FROM pg_database WHERE datname = %s", (database_name,))
        exists = cursor.fetchone()
        if not exists:
            cursor.execute(f'CREATE DATABASE "{database_name}"')
            print(f"created database: {database_name}")
        else:
            print(f"database exists: {database_name}")


def run_migrations() -> None:
    with get_connection() as conn:
        cursor = conn.cursor()
        for path in sorted(MIGRATION_DIR.glob("*.sql")):
            sql = path.read_text(encoding="utf-8")
            try:
                cursor.execute(sql)
                print(f"migration applied: {path.name}")
            except Exception as exc:
                if "vector" in str(exc).lower():
                    raise RuntimeError(
                        "pgvector 扩展不可用。请先在 PostgreSQL 安装 pgvector，"
                        "然后重新运行 py -3 backend/scripts/init_db.py"
                    ) from exc
                raise


def main() -> None:
    load_dotenv(ROOT / "backend" / ".env")
    ensure_database()
    run_migrations()


if __name__ == "__main__":
    main()
