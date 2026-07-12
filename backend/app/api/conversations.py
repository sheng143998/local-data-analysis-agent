from uuid import UUID

from fastapi import APIRouter, Depends

from backend.app.api.dependencies import get_current_principal, require_role
from backend.app.schemas.analysis import ConversationDetail, ConversationSummary
from backend.app.schemas.auth import AuthPrincipal
from backend.app.services.agent_service import AgentService


router = APIRouter(prefix="/conversations", tags=["conversations"])
conversation_service = AgentService()


@router.get("", response_model=list[ConversationSummary])
def list_conversations(limit: int = 20, principal: AuthPrincipal = Depends(get_current_principal)) -> list[ConversationSummary]:
    return conversation_service.list_conversations(_owner_id(principal), limit)


@router.get("/{conversation_id}", response_model=ConversationDetail)
def get_conversation(conversation_id: UUID, principal: AuthPrincipal = Depends(get_current_principal)) -> ConversationDetail:
    return conversation_service.get_conversation(conversation_id, _owner_id(principal))


@router.post("/claim-development", dependencies=[Depends(require_role("admin"))])
def claim_development_conversations(principal: AuthPrincipal = Depends(get_current_principal)) -> dict[str, int]:
    if principal.is_development_principal:
        return {"claimed": 0}
    return {"claimed": conversation_service.claim_development_conversations(principal.id)}


def _owner_id(principal: AuthPrincipal) -> UUID | None:
    return None if principal.is_development_principal else principal.id
