import json
from datetime import datetime, timedelta, timezone
from typing import Protocol
from uuid import UUID

from backend.app.core.config import settings
from backend.app.db.repositories.conversation_repository import ConversationRepository
from backend.app.schemas.conversation import ConversationState


class ConversationStore(Protocol):
    def get(self, conversation_id: UUID) -> ConversationState | None: ...
    def save(self, state: ConversationState) -> None: ...
    def list_for_owner(self, owner_id: UUID | None, limit: int) -> list[ConversationState]: ...
    def claim_development_conversations(self, owner_id: UUID) -> int: ...


class InMemoryConversationStore:
    """Development/test fallback. It intentionally does not survive process restarts."""

    def __init__(self) -> None:
        self._items: dict[UUID, tuple[ConversationState, datetime]] = {}

    def get(self, conversation_id: UUID) -> ConversationState | None:
        self._purge()
        item = self._items.get(conversation_id)
        return item[0] if item else None

    def save(self, state: ConversationState) -> None:
        self._items[state.id] = (state, self._expires_at())

    def list_for_owner(self, owner_id: UUID | None, limit: int) -> list[ConversationState]:
        self._purge()
        return sorted(
            (state for state, _ in self._items.values() if state.owner_id == owner_id),
            key=lambda item: item.updated_at,
            reverse=True,
        )[:limit]

    def claim_development_conversations(self, owner_id: UUID) -> int:
        claimed = 0
        for conversation_id, (state, expires_at) in list(self._items.items()):
            if state.owner_id is None:
                self._items[conversation_id] = (state.model_copy(update={"owner_id": owner_id}), expires_at)
                claimed += 1
        return claimed

    def _expires_at(self) -> datetime:
        return datetime.now(timezone.utc) + timedelta(hours=settings.conversation_retention_hours)

    def _purge(self) -> None:
        now = datetime.now(timezone.utc)
        for key, (_, expires_at) in list(self._items.items()):
            if expires_at <= now:
                self._items.pop(key, None)


class RedisConversationStore:
    def __init__(self, redis_client, repository: ConversationRepository | None = None) -> None:
        self._redis = redis_client
        self._repository = repository or ConversationRepository()

    def get(self, conversation_id: UUID) -> ConversationState | None:
        # 持久化副本优先，确保管理员迁移归属后不会读到 Redis 的旧 owner。
        persisted = self._repository.get(conversation_id)
        if persisted is not None:
            return persisted
        try:
            payload = self._redis.get(self._key(conversation_id))
        except Exception:  # noqa: BLE001 - Redis 是加速层，故障时必须降级到持久化副本
            payload = None
        if payload:
            return ConversationState.model_validate_json(payload)
        return None

    def save(self, state: ConversationState) -> None:
        # 数据库副本用于 Redis 停止、重启或过期时的会话恢复，保留相同的三天生命周期。
        self._repository.save(state)
        encoded = state.model_dump_json()
        ttl = settings.conversation_retention_hours * 60 * 60
        owner_key = self._owner_key(state.owner_id)
        try:
            pipeline = self._redis.pipeline(transaction=False)
            pipeline.set(self._key(state.id), encoded, ex=ttl)
            pipeline.zadd(owner_key, {str(state.id): state.updated_at.timestamp()})
            pipeline.expire(owner_key, ttl)
            pipeline.execute()
        except Exception:
            # Redis 不可用时数据库副本已保存，会话请求不能因此丢失。
            return

    def list_for_owner(self, owner_id: UUID | None, limit: int) -> list[ConversationState]:
        # 列表以数据库副本为准，避免 Redis 失效后历史列表突然变空。
        return self._repository.list_for_owner(owner_id, limit)

    def claim_development_conversations(self, owner_id: UUID) -> int:
        return self._repository.claim_development_conversations(owner_id)

    @staticmethod
    def _key(conversation_id: UUID) -> str:
        return f"conversation:{conversation_id}"

    @staticmethod
    def _owner_key(owner_id: UUID | None) -> str:
        return f"conversation-owner:{owner_id or 'development'}"


_memory_store = InMemoryConversationStore()
_store: ConversationStore | None = None


def get_conversation_store() -> ConversationStore:
    global _store
    if _store is not None:
        return _store
    if settings.redis_url:
        try:
            import redis

            client = redis.Redis.from_url(settings.redis_url, decode_responses=True, socket_connect_timeout=0.2, socket_timeout=0.5)
            client.ping()
            _store = RedisConversationStore(client)
            return _store
        except Exception:
            if settings.app_env in {"production", "prod"}:
                raise RuntimeError("Redis is required for production conversation memory")
    try:
        _store = PostgresConversationStore()
        return _store
    except Exception:
        _store = _memory_store
        return _store


def reset_conversation_store_for_tests() -> None:
    global _store
    _store = InMemoryConversationStore()


class PostgresConversationStore:
    """Redis 不可用时的本地恢复层，不将会话降级为易失内存。"""

    def __init__(self, repository: ConversationRepository | None = None) -> None:
        self._repository = repository or ConversationRepository()

    def get(self, conversation_id: UUID) -> ConversationState | None:
        return self._repository.get(conversation_id)

    def save(self, state: ConversationState) -> None:
        self._repository.save(state)

    def list_for_owner(self, owner_id: UUID | None, limit: int) -> list[ConversationState]:
        return self._repository.list_for_owner(owner_id, limit)

    def claim_development_conversations(self, owner_id: UUID) -> int:
        return self._repository.claim_development_conversations(owner_id)
