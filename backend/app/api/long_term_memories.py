from fastapi import APIRouter, Depends, HTTPException

from backend.app.api.dependencies import get_current_principal, require_csrf
from backend.app.schemas.auth import AuthPrincipal
from backend.app.schemas.long_term_memory import LongTermMemory
from backend.app.services.long_term_memory_service import LongTermMemoryService


router = APIRouter(prefix="/user-memories", tags=["user-memories"])
memory_service = LongTermMemoryService()


@router.get("", response_model=list[LongTermMemory])
def list_user_memories(principal: AuthPrincipal = Depends(get_current_principal)) -> list[LongTermMemory]:
    if principal.is_development_principal:
        return []
    return memory_service.list_memories(principal.id)


@router.delete("/{memory_key}", response_model=dict[str, bool], dependencies=[Depends(require_csrf)])
def delete_user_memory(memory_key: str, principal: AuthPrincipal = Depends(get_current_principal)) -> dict[str, bool]:
    if principal.is_development_principal or not memory_service.forget(principal.id, memory_key):
        raise HTTPException(status_code=404, detail="长期偏好不存在")
    return {"deleted": True}
