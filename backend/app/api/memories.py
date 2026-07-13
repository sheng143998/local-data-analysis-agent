from uuid import UUID

from fastapi import APIRouter, Depends

from backend.app.api.dependencies import require_role
from backend.app.schemas.memories import SqlMemoryRecord, SqlMemoryTrustUpdate
from backend.app.services.memory_service import MemoryService


router = APIRouter(prefix="/memories", tags=["memories"])
memory_service = MemoryService()


@router.get("", response_model=list[SqlMemoryRecord], dependencies=[Depends(require_role("admin"))])
def list_memories(limit: int = 50) -> list[SqlMemoryRecord]:
    return memory_service.list_memories(limit)


@router.get("/{memory_id}", response_model=SqlMemoryRecord, dependencies=[Depends(require_role("admin"))])
def get_memory(memory_id: UUID) -> SqlMemoryRecord:
    return memory_service.get_memory(memory_id)


@router.patch("/{memory_id}/trust", response_model=SqlMemoryRecord, dependencies=[Depends(require_role("admin"))])
def update_memory_trust(memory_id: UUID, payload: SqlMemoryTrustUpdate) -> SqlMemoryRecord:
    return memory_service.update_trust_status(memory_id, payload.trust_status)
