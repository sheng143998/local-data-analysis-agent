import hashlib
import time
from collections import defaultdict

from fastapi import HTTPException, Request

from backend.app.core.config import settings


class AuthRateLimiter:
    """Login protection is intentionally separate from conversation-state concurrency."""

    def __init__(self) -> None:
        self._memory_attempts: dict[str, list[float]] = defaultdict(list)
        self._redis = None

    def enforce(self, action: str, request: Request, email: str, limit: int, window_seconds: int) -> None:
        key = self._key(action, request, email)
        try:
            count = self._redis_increment(key, window_seconds)
        except Exception:
            if settings.app_env in {"production", "prod"}:
                raise HTTPException(status_code=503, detail="认证保护服务暂时不可用")
            count = self._memory_increment(key, window_seconds)
        if count > limit:
            raise HTTPException(status_code=429, detail="尝试次数过多，请稍后再试")

    def _redis_increment(self, key: str, window_seconds: int) -> int:
        if self._redis is None:
            import redis

            self._redis = redis.Redis.from_url(settings.redis_url, decode_responses=True, socket_connect_timeout=0.2, socket_timeout=0.5)
        count = int(self._redis.incr(key))
        if count == 1:
            self._redis.expire(key, window_seconds)
        return count

    def _memory_increment(self, key: str, window_seconds: int) -> int:
        now = time.monotonic()
        attempts = [item for item in self._memory_attempts[key] if now - item < window_seconds]
        attempts.append(now)
        self._memory_attempts[key] = attempts
        return len(attempts)

    @staticmethod
    def _key(action: str, request: Request, email: str) -> str:
        source = f"{action}:{email.lower()}:{request.client.host if request.client else ''}"
        return "auth-rate:" + hashlib.sha256(source.encode("utf-8")).hexdigest()


auth_rate_limiter = AuthRateLimiter()
