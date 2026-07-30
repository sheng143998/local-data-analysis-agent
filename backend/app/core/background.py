"""关键路径外的后台簿记执行器。

记忆写回与运行日志属于"响应之后"的工作（实测约 4.6s + 若干次落库），
不应占用用户可感知的延迟。BOOKKEEPING_ASYNC=true 时这些任务提交到
这里的有界线程池；测试或需要严格同步的场景置 false 即可完全绕开。
"""
from __future__ import annotations

import atexit
import logging
import threading
from concurrent.futures import Future, ThreadPoolExecutor
from typing import Callable

logger = logging.getLogger("backend.background")

_MAX_WORKERS = 2

_executor: ThreadPoolExecutor | None = None
_executor_lock = threading.Lock()
_pending: set[Future] = set()
_pending_lock = threading.Lock()


def _get_executor() -> ThreadPoolExecutor:
    global _executor
    with _executor_lock:
        if _executor is None:
            _executor = ThreadPoolExecutor(max_workers=_MAX_WORKERS, thread_name_prefix="bookkeeping")
        return _executor


def submit_bookkeeping(task: Callable[[], None], *, description: str = "bookkeeping") -> Future:
    """提交一个无参簿记任务；异常只记日志，绝不冒泡到请求线程。"""

    def _runner() -> None:
        try:
            task()
        except Exception:  # noqa: BLE001 - 簿记失败不能影响主流程
            logger.warning("background task failed: %s", description, exc_info=True)

    future = _get_executor().submit(_runner)
    with _pending_lock:
        _pending.add(future)
    future.add_done_callback(_discard_pending)
    return future


def _discard_pending(future: Future) -> None:
    with _pending_lock:
        _pending.discard(future)


def wait_for_idle(timeout: float = 10.0) -> bool:
    """等待所有已提交任务完成（测试与优雅停机用）。返回是否全部完成。"""
    import time

    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        with _pending_lock:
            if not _pending:
                return True
        time.sleep(0.02)
    with _pending_lock:
        return not _pending


def shutdown() -> None:
    global _executor
    with _executor_lock:
        executor, _executor = _executor, None
    if executor is not None:
        executor.shutdown(wait=False)


atexit.register(shutdown)
