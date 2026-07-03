from fastapi import APIRouter

from backend.app.api.metrics import router as metrics_router
from backend.app.schemas.analysis import AnalyzeRequest, AnalyzeResponse
from backend.app.services.agent_service import AgentService


router = APIRouter()
agent_service = AgentService()
router.include_router(metrics_router)


@router.get("/health")
def health() -> dict[str, str | bool]:
    return {"ok": True, "service": "local-data-analysis-agent", "version": "0.1.0"}


@router.post("/analyze", response_model=AnalyzeResponse)
def analyze(payload: AnalyzeRequest) -> AnalyzeResponse:
    return agent_service.analyze(payload)
