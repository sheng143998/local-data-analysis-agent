import re
from uuid import UUID

from backend.app.db.repositories.long_term_memory_repository import LongTermMemoryRepository
from backend.app.schemas.long_term_memory import LongTermMemory, RememberedPreference


class LongTermMemoryService:
    def __init__(self, repository: LongTermMemoryRepository | None = None) -> None:
        self.repository = repository or LongTermMemoryRepository()

    def list_memories(self, user_id: UUID) -> list[LongTermMemory]:
        return self.repository.list_active(user_id)

    def forget(self, user_id: UUID, memory_key: str) -> bool:
        return self.repository.revoke(user_id, memory_key)

    def handle_explicit_preference(self, user_id: UUID, text: str, conversation_id: UUID | None = None) -> str | None:
        forget_key = _forget_key(text)
        if forget_key:
            self.repository.revoke(user_id, forget_key)
            return "已忘记这项长期偏好。"
        preference = _extract_preference(text)
        if preference is None:
            return None
        memory = self.repository.remember(user_id, preference, conversation_id)
        return f"已记住：以后默认{memory.value.get('label', memory.value.get('value', '使用该偏好'))}。"

    def context_for(self, user_id: UUID | None, question: str) -> str:
        if user_id is None:
            return ""
        memories = self.repository.list_active(user_id)
        relevant = [memory for memory in memories if memory.memory_key in {"currency", "default_granularity"}]
        return "\n".join(
            f"长期偏好 {memory.memory_key}={memory.value.get('value', '')}" for memory in relevant[:3]
        )


def _extract_preference(text: str) -> RememberedPreference | None:
    if not any(token in text for token in ("记住", "默认", "偏好", "以后")):
        return None
    if "人民币" in text:
        return RememberedPreference(memory_key="currency", category="presentation", value={"value": "CNY", "label": "使用人民币展示金额"})
    if "美元" in text:
        return RememberedPreference(memory_key="currency", category="presentation", value={"value": "USD", "label": "使用美元展示金额"})
    if re.search(r"默认.*(按月|每月|月度)", text):
        return RememberedPreference(memory_key="default_granularity", category="analysis", value={"value": "month", "label": "按月汇总"})
    if re.search(r"默认.*(按天|每天|日度)", text):
        return RememberedPreference(memory_key="default_granularity", category="analysis", value={"value": "day", "label": "按天汇总"})
    return None


def _forget_key(text: str) -> str | None:
    if not any(token in text for token in ("忘记", "删除偏好", "清除偏好")):
        return None
    if any(token in text for token in ("货币", "人民币", "美元")):
        return "currency"
    if any(token in text for token in ("按月", "按天", "粒度")):
        return "default_granularity"
    return None
