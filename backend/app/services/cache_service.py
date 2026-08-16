"""查询结果缓存服务：Redis 优先，Redis 不可用时降级为进程内 LRU。

业务目的：对 Guard 放行后的成功查询结果做短 TTL 缓存，降低重复问题的
EXPLAIN 与数据库执行开销。缓存内容只包含已 JSON 化的结果，不保存
Prompt、密钥、原始错误或未脱敏样本。
"""
from __future__ import annotations

import json
import threading
import time
from collections import OrderedDict
from typing import Any

from backend.app.core.config import settings


class CacheService:
    """轻量查询结果缓存。

    - Redis 可用时使用 Redis，支持多进程共享。
    - Redis 不可用时自动降级为进程内 LRU，保证本地开发可用。
    - 所有方法在 Redis 异常时都不会抛出，避免缓存故障影响主链路。
    """

    def __init__(
        self,
        redis_url: str | None = None,
        *,
        prefix: str | None = None,
        default_ttl: int | None = None,
        max_entries: int | None = None,
    ) -> None:
        self._redis_url = redis_url or settings.redis_url
        self._prefix = prefix or settings.query_cache_prefix
        self._default_ttl = settings.query_cache_ttl_seconds if default_ttl is None else default_ttl
        self._max_entries = settings.query_cache_max_entries if max_entries is None else max_entries
        self._redis: Any = None
        self._memory: "OrderedDict[str, tuple[str, float | None]]" = OrderedDict()
        self._lock = threading.RLock()
        self._init_redis()

    def _init_redis(self) -> None:
        if not self._redis_url:
            return
        try:
            import redis

            client = redis.Redis.from_url(
                self._redis_url,
                decode_responses=True,
                socket_connect_timeout=0.2,
                socket_timeout=0.5,
            )
            client.ping()
            self._redis = client
        except Exception:
            # Redis 只是加速层，不可用时降级到进程内 LRU，不阻塞查询链路。
            self._redis = None

    def get(self, key: str) -> Any | None:
        if self._redis is not None:
            try:
                raw = self._redis.get(self._full_key(key))
                if raw is None:
                    return None
                return json.loads(raw)
            except Exception:
                pass

        with self._lock:
            item = self._memory.get(key)
            if item is None:
                return None
            payload, expires_at = item
            if expires_at is not None and expires_at < time.time():
                self._memory.pop(key, None)
                return None
            self._memory.move_to_end(key)
            return json.loads(payload)

    def set(self, key: str, value: Any, ttl: int | None = None) -> None:
        payload = json.dumps(value, ensure_ascii=False, separators=(",", ":"))
        effective_ttl = self._default_ttl if ttl is None else ttl

        if self._redis is not None:
            try:
                self._redis.set(
                    self._full_key(key),
                    payload,
                    ex=effective_ttl if effective_ttl and effective_ttl > 0 else None,
                )
                return
            except Exception:
                pass

        with self._lock:
            expires_at = time.time() + effective_ttl if effective_ttl and effective_ttl > 0 else None
            self._memory[key] = (payload, expires_at)
            self._memory.move_to_end(key)
            while len(self._memory) > self._max_entries:
                self._memory.popitem(last=False)

    def delete_prefix(self, prefix: str) -> int:
        """删除指定前缀的缓存项；prefix 为空时清空全部。"""
        deleted = 0

        if self._redis is not None:
            try:
                full_prefix = self._full_key(prefix) + "*"
                cursor = 0
                while True:
                    cursor, keys = self._redis.scan(cursor, match=full_prefix, count=200)
                    if keys:
                        deleted += self._redis.delete(*keys)
                    if cursor == 0:
                        break
            except Exception:
                pass

        with self._lock:
            matching = [key for key in self._memory if key.startswith(prefix)]
            for key in matching:
                self._memory.pop(key, None)
                deleted += 1
        return deleted

    def clear_all(self) -> int:
        return self.delete_prefix("")

    def _full_key(self, key: str) -> str:
        if key.startswith(self._prefix):
            return key
        return f"{self._prefix}:{key}"


_cache_service: CacheService | None = None
_cache_service_lock = threading.Lock()


def get_cache_service() -> CacheService:
    """返回进程内单例缓存服务，保证测试可重置。"""
    global _cache_service
    if _cache_service is None:
        with _cache_service_lock:
            if _cache_service is None:
                _cache_service = CacheService()
    return _cache_service


def reset_cache_service_for_tests() -> None:
    """测试隔离用：清空单例，使下一次获取重新初始化。"""
    global _cache_service
    _cache_service = None
