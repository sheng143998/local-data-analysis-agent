from uuid import UUID

from fastapi import APIRouter

from backend.app.schemas.runs import QueryRunDetail, QueryRunRecord
from backend.app.services.run_service import RunService


router = APIRouter(prefix="/runs", tags=["runs"])
run_service = RunService()


@router.get("", response_model=list[QueryRunRecord])
def list_runs(limit: int = 20) -> list[QueryRunRecord]:
    return run_service.list_runs(limit)


@router.get("/{run_id}", response_model=QueryRunDetail)
def get_run(run_id: UUID) -> QueryRunDetail:
    return run_service.get_run(run_id)
