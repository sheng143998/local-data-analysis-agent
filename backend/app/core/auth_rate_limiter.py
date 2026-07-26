import hashlib
import time
from collections import defaultdict

from fastapi import HTTPException, Request

from backend.app.core.config import settings


_MEMORY_SWEEP_THRESHOLD = 4096


class AuthRateLimiter:
    """Login protection is intentionally separate from conversation-state concurrency."""

    def __init__(self) -> None:
        self._memory_attempts: dict[str, list[float]] = defaultdict(list)
        self._memory_windows: dict[str, int] = {}
        self._redis = None

    def enforce(self, action: str, request: Request, email: str, limit: int, window_seconds: int) -> None:
        """计一次尝试并校验限额（注册等所有尝试都应计数的场景）。"""
        key = self._key(action, request, email)
        count = self._increment(key, window_seconds)
        if count > limit:
            raise HTTPException(status_code=429, detail="尝试次数过多，请稍后再试")

    def check(self, action: str, request: Request, email: str, limit: int, window_seconds: int) -> None:
        """只校验不计数：登录成功不应消耗限额，失败由 record_failure 计数。"""
        key = self._key(action, request, email)
        try:
            count = self._redis_count(key)
        except Exception:
            self._require_redis_in_production()
            count = self._memory_count(key, window_seconds)
        if count >= limit:
            raise HTTPException(status_code=429, detail="尝试次数过多，请稍后再试")

    def record_failure(self, action: str, request: Request, email: str, window_seconds: int) -> None:
        key = self._key(action, request, email)
        self._increment(key, window_seconds)

    def _increment(self, key: str, window_seconds: int) -> int:
        try:
            return self._redis_increment(key, window_seconds)
        except Exception:
            self._require_redis_in_production()
            return self._memory_increment(key, window_seconds)

    def _require_redis_in_production(self) -> None:
        if settings.app_env in {"production", "prod"}:
            raise HTTPException(status_code=503, detail="认证保护服务暂时不可用")

    def _redis_client(self):
        if self._redis is None:
            import redis

            self._redis = redis.Redis.from_url(settings.redis_url, decode_responses=True, socket_connect_timeout=0.2, socket_timeout=0.5)
        return self._redis

    def _redis_increment(self, key: str, window_seconds: int) -> int:
        client = self._redis_client()
        count = int(client.incr(key))
        if count == 1:
            client.expire(key, window_seconds)
        return count

    def _redis_count(self, key: str) -> int:
        value = self._redis_client().get(key)
        return int(value) if value else 0

    def _memory_increment(self, key: str, window_seconds: int) -> int:
        now = time.monotonic()
        attempts = [item for item in self._memory_attempts[key] if now - item < window_seconds]
        attempts.append(now)
        self._memory_attempts[key] = attempts
        self._memory_windows[key] = window_seconds
        self._maybe_sweep_memory(now)
        return len(attempts)

    def _memory_count(self, key: str, window_seconds: int) -> int:
        now = time.monotonic()
        attempts = [item for item in self._memory_attempts.get(key, []) if now - item < window_seconds]
        if attempts:
            self._memory_attempts[key] = attempts
            self._memory_windows[key] = window_seconds
        else:
            self._memory_attempts.pop(key, None)
            self._memory_windows.pop(key, None)
        return len(attempts)

    def _maybe_sweep_memory(self, now: float) -> None:
        """撞库场景下 key 会无限增长；超过阈值时清理已全部过期的 key。"""
        if len(self._memory_attempts) <= _MEMORY_SWEEP_THRESHOLD:
            return
        expired = [
            key
            for key, attempts in self._memory_attempts.items()
            if not attempts
            or all(now - item >= self._memory_windows.get(key, 3600) for item in attempts)
        ]
        for key in expired:
            self._memory_attempts.pop(key, None)
            self._memory_windows.pop(key, None)

    @staticmethod
    def _key(action: str, request: Request, email: str) -> str:
        source = f"{action}:{email.lower()}:{request.client.host if request.client else ''}"
        return "auth-rate:" + hashlib.sha256(source.encode("utf-8")).hexdigest()


auth_rate_limiter = AuthRateLimiter()
