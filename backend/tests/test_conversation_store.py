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


class FakeConversationRepository:
    def __init__(self) -> None:
        self.states = {}

    def get(self, conversation_id):
        return self.states.get(conversation_id)

    def save(self, state) -> None:
        self.states[state.id] = state

    def list_for_owner(self, owner_id, limit, cursor=None):
        states = sorted(
            (state for state in self.states.values() if state.owner_id == owner_id),
            key=lambda state: (state.updated_at, str(state.id)),
            reverse=True,
        )
        if cursor is not None:
            states = [
                state
                for state in states
                if (state.updated_at, str(state.id)) < (cursor[0], str(cursor[1]))
            ]
        return states[:limit]

    def claim_development_conversations(self, owner_id):
        claimed = 0
        for conversation_id, state in list(self.states.items()):
            if state.owner_id is None:
                self.states[conversation_id] = state.model_copy(update={"owner_id": owner_id})
                claimed += 1
        return claimed


def test_redis_store_round_trips_owner_scoped_conversation() -> None:
    redis = FakeRedis()
    store = RedisConversationStore(redis, repository=FakeConversationRepository())
    owner = uuid4()
    now = datetime.now(timezone.utc)
    state = ConversationState(id=uuid4(), owner_id=owner, title="conversation", created_at=now, updated_at=now)

    store.save(state)

    assert store.get(state.id).id == state.id
    assert [item.id for item in store.list_for_owner(owner, 20)] == [state.id]
    assert store.list_for_owner(uuid4(), 20) == []
