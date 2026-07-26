"""进程级共享 httpx.Client。

每次模型/Embedding 调用都新建 Client 会丢弃 keep-alive 与 TLS 会话，
对远程 provider 意味着每次调用都要完整 TCP+TLS 握手。httpx.Client
本身线程安全，这里按 trust_env 维度缓存复用。
"""
from __future__ import annotations

import atexit
import threading

import httpx

RETRYABLE_STATUS_CODES = {408, 429}

_clients: dict[bool, httpx.Client] = {}
_clients_lock = threading.Lock()


def shared_client(*, trust_env: bool = True) -> httpx.Client:
    with _clients_lock:
        client = _clients.get(trust_env)
        if client is None or client.is_closed:
            client = httpx.Client(trust_env=trust_env)
            _clients[trust_env] = client
        return client


def is_retryable_status(status_code: int) -> bool:
    """只重试瞬态错误：408/429 与 5xx。401/404/422 等确定性失败立即返回。"""
    return status_code in RETRYABLE_STATUS_CODES or status_code >= 500


def close_shared_clients() -> None:
    with _clients_lock:
        clients = list(_clients.values())
        _clients.clear()
    for client in clients:
        try:
            client.close()
        except Exception:
            pass


atexit.register(close_shared_clients)
