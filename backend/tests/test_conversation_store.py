from datetime import datetime, timezone
from uuid import uuid4

from backend.app.schemas.conversation import ConversationState
from backend.app.services.conversation_store import RedisConversationStore


class FakePipeline:
    def __init__(self, redis) -> None:
        self.redis = redis
        self.operations = []

    def set(self, *args, **kwargs): self.operations.append(("set", args, kwargs)); return self
    def zadd(self, *args, **kwargs): self.operations.append(("zadd", args, kwargs)); return self
    def expire(self, *args, **kwargs): self.operations.append(("expire", args, kwargs)); return self
    def execute(self):
        for name, args, kwargs in self.operations:
            getattr(self.redis, name)(*args, **kwargs)


class FakeRedis:
    def __init__(self) -> None:
        self.values = {}
        self.sorted_sets = {}

    def pipeline(self, **_kwargs): return FakePipeline(self)
    def set(self, key, value, **_kwargs): self.values[key] = value
    def zadd(self, key, values): self.sorted_sets.setdefault(key, {}).update(values)
    def expire(self, *_args, **_kwargs): pass
    def get(self, key): return self.values.get(key)
    def zrevrange(self, key, start, end):
        values = sorted(self.sorted_sets.get(key, {}).items(), key=lambda item: item[1], reverse=True)
        return [item[0] for item in values[start:end + 1]]


def test_redis_store_round_trips_owner_scoped_conversation() -> None:
    redis = FakeRedis()
    store = RedisConversationStore(redis)
    owner = uuid4()
    now = datetime.now(timezone.utc)
    state = ConversationState(id=uuid4(), owner_id=owner, title="conversation", created_at=now, updated_at=now)

    store.save(state)

    assert store.get(state.id).id == state.id
    assert [item.id for item in store.list_for_owner(owner, 20)] == [state.id]
    assert store.list_for_owner(uuid4(), 20) == []
