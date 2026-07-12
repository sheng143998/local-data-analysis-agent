from uuid import UUID

from fastapi import APIRouter, Depends

from backend.app.api.dependencies import require_csrf, require_role
from backend.app.schemas.metrics import MetricCreate, MetricDefinition, MetricUpdate
from backend.app.services.metric_service import MetricService


router = APIRouter(prefix="/metrics", tags=["metrics"])
metric_service = MetricService()


@router.get("", response_model=list[MetricDefinition])
def list_metrics() -> list[MetricDefinition]:
    return metric_service.list_metrics()


@router.get("/{metric_id}", response_model=MetricDefinition)
def get_metric(metric_id: UUID) -> MetricDefinition:
    return metric_service.get_metric(metric_id)


@router.post("", response_model=MetricDefinition, dependencies=[Depends(require_role("admin")), Depends(require_csrf)])
def create_metric(payload: MetricCreate) -> MetricDefinition:
    return metric_service.create_metric(payload)


@router.put("/{metric_id}", response_model=MetricDefinition, dependencies=[Depends(require_role("admin")), Depends(require_csrf)])
def update_metric(metric_id: UUID, payload: MetricUpdate) -> MetricDefinition:
    return metric_service.update_metric(metric_id, payload)


@router.delete("/{metric_id}", response_model=dict[str, bool], dependencies=[Depends(require_role("admin")), Depends(require_csrf)])
def delete_metric(metric_id: UUID) -> dict[str, bool]:
    return metric_service.delete_metric(metric_id)
