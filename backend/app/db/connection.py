import atexit
import os
import threading
from contextlib import contextmanager
from pathlib import Path
from queue import Empty, Full, Queue
from typing import Iterator
from urllib.parse import urlparse

import pg8000.dbapi
from dotenv import load_dotenv


# 相对 CWD 的路径在从其他目录启动（Windows 服务、计划任务）时会静默失效，
# 这里固定解析到仓库内的 backend/.env。
_ENV_PATH = Path(__file__).resolve().parents[2] / ".env"
load_dotenv(_ENV_PATH)

# 每个目标数据库一个有界连接池，避免每条查询付出完整 TCP + 认证握手。
_POOL_SIZE = max(1, int(os.getenv("DB_POOL_SIZE", "5")))
_pools: dict[str, Queue] = {}
_pools_lock = threading.Lock()


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


def _pool_for(url: str) -> Queue:
    with _pools_lock:
        pool = _pools.get(url)
        if pool is None:
            pool = Queue(maxsize=_POOL_SIZE)
            _pools[url] = pool
        return pool


def _new_connection(url: str) -> pg8000.dbapi.Connection:
    conn = pg8000.dbapi.connect(**parse_database_url(url))
    conn.autocommit = True
    return conn


def _reset_for_reuse(conn: pg8000.dbapi.Connection) -> bool:
    """归还前把连接恢复为干净状态；失败则视为损坏，不再复用。"""
    try:
        conn.rollback()
        return True
    except Exception:
        try:
            conn.close()
        except Exception:
            pass
        return False


@contextmanager
def get_connection(database: str | None = None) -> Iterator[pg8000.dbapi.Connection]:
    """借出一个池化连接（autocommit 开启）；使用方接口与旧版保持一致。

    出现任何异常时该连接会被丢弃而不是归还，避免把损坏或处于
    未知事务状态的连接泄漏给后续调用方。
    """
    url = get_database_url(database)
    pool = _pool_for(url)
    try:
        conn = pool.get_nowait()
    except Empty:
        conn = _new_connection(url)

    try:
        yield conn
    except Exception:
        try:
            conn.close()
        except Exception:
            pass
        raise
    else:
        if _reset_for_reuse(conn):
            try:
                pool.put_nowait(conn)
            except Full:
                try:
                    conn.close()
                except Exception:
                    pass


def close_all_pools() -> None:
    """关闭所有空闲池连接（进程退出与测试清理用）。"""
    with _pools_lock:
        pools = list(_pools.values())
        _pools.clear()
    for pool in pools:
        while True:
            try:
                conn = pool.get_nowait()
            except Empty:
                break
            try:
                conn.close()
            except Exception:
                pass


atexit.register(close_all_pools)
