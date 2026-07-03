from uuid import UUID

from fastapi import HTTPException

from backend.app.db.repositories.memory_repository import SqlMemoryRepository
from backend.app.schemas.memories import SqlMemoryRecord


class MemoryService:
    def __init__(self, repository: SqlMemoryRepository | None = None) -> None:
        self.repository = repository or SqlMemoryRepository()

    def list_memories(self, limit: int = 50) -> list[SqlMemoryRecord]:
        safe_limit = min(max(limit, 1), 100)
        return self.repository.list(safe_limit)

    def get_memory(self, memory_id: UUID) -> SqlMemoryRecord:
        memory = self.repository.get(memory_id)
        if memory is None:
            raise HTTPException(status_code=404, detail="SQL Memory 不存在")
        return memory
