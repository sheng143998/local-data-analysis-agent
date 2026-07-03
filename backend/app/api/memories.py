from uuid import UUID

from fastapi import APIRouter

from backend.app.schemas.memories import SqlMemoryRecord
from backend.app.services.memory_service import MemoryService


router = APIRouter(prefix="/memories", tags=["memories"])
memory_service = MemoryService()


@router.get("", response_model=list[SqlMemoryRecord])
def list_memories(limit: int = 50) -> list[SqlMemoryRecord]:
    return memory_service.list_memories(limit)


@router.get("/{memory_id}", response_model=SqlMemoryRecord)
def get_memory(memory_id: UUID) -> SqlMemoryRecord:
    return memory_service.get_memory(memory_id)
