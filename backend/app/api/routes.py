from fastapi import APIRouter, HTTPException

from backend.app.api.memories import router as memories_router
from backend.app.api.metrics import router as metrics_router
from backend.app.api.runs import router as runs_router
from backend.app.schemas.analysis import AnalyzeRequest, AnalyzeResponse
from backend.app.services.agent_service import AgentService, AnalysisUnavailableError


router = APIRouter()
agent_service = AgentService()
router.include_router(memories_router)
router.include_router(metrics_router)
router.include_router(runs_router)


@router.get("/health")
def health() -> dict[str, str | bool]:
    return {"ok": True, "service": "local-data-analysis-agent", "version": "0.1.0"}


@router.post("/analyze", response_model=AnalyzeResponse)
def analyze(payload: AnalyzeRequest) -> AnalyzeResponse:
    try:
        return agent_service.analyze(payload)
    except AnalysisUnavailableError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
