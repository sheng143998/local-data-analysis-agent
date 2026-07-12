import json
from datetime import datetime, timedelta, timezone
from typing import Protocol
from uuid import UUID

from backend.app.core.config import settings
from backend.app.schemas.conversation import ConversationState


class ConversationStore(Protocol):
    def get(self, conversation_id: UUID) -> ConversationState | None: ...
    def save(self, state: ConversationState) -> None: ...
    def list_for_owner(self, owner_id: UUID | None, limit: int) -> list[ConversationState]: ...


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

    def _expires_at(self) -> datetime:
        return datetime.now(timezone.utc) + timedelta(hours=settings.conversation_retention_hours)

    def _purge(self) -> None:
        now = datetime.now(timezone.utc)
        for key, (_, expires_at) in list(self._items.items()):
            if expires_at <= now:
                self._items.pop(key, None)


class RedisConversationStore:
    def __init__(self, redis_client) -> None:
        self._redis = redis_client

    def get(self, conversation_id: UUID) -> ConversationState | None:
        payload = self._redis.get(self._key(conversation_id))
        if not payload:
            return None
        return ConversationState.model_validate_json(payload)

    def save(self, state: ConversationState) -> None:
        encoded = state.model_dump_json()
        ttl = settings.conversation_retention_hours * 60 * 60
        owner_key = self._owner_key(state.owner_id)
        pipeline = self._redis.pipeline(transaction=False)
        pipeline.set(self._key(state.id), encoded, ex=ttl)
        pipeline.zadd(owner_key, {str(state.id): state.updated_at.timestamp()})
        pipeline.expire(owner_key, ttl)
        pipeline.execute()

    def list_for_owner(self, owner_id: UUID | None, limit: int) -> list[ConversationState]:
        ids = self._redis.zrevrange(self._owner_key(owner_id), 0, max(limit - 1, 0))
        states = [self.get(UUID(value)) for value in ids]
        return [state for state in states if state is not None and state.owner_id == owner_id]

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
    _store = _memory_store
    return _store


def reset_conversation_store_for_tests() -> None:
    global _store
    _store = InMemoryConversationStore()
