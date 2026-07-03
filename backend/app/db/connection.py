import os
from contextlib import contextmanager
from typing import Iterator
from urllib.parse import urlparse

import pg8000.dbapi
from dotenv import load_dotenv


load_dotenv("backend/.env")


def get_database_url(database: str | None = None) -> str:
    url = os.getenv("DATABASE_URL")
    if not url:
        raise RuntimeError("DATABASE_URL 未配置，请先创建 backend/.env")
    if database is None:
        return url
    return url.rsplit("/", 1)[0] + f"/{database}"


def parse_database_url(url: str) -> dict[str, str | int]:
    parsed = urlparse(url)
    return {
        "user": parsed.username or "",
        "password": parsed.password or "",
        "host": parsed.hostname or "127.0.0.1",
        "port": parsed.port or 5432,
        "database": parsed.path.lstrip("/") or "postgres",
    }


@contextmanager
def get_connection(database: str | None = None) -> Iterator[pg8000.dbapi.Connection]:
    config = parse_database_url(get_database_url(database))
    conn = pg8000.dbapi.connect(**config)
    conn.autocommit = True
    try:
        yield conn
    finally:
        conn.close()
