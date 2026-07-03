from uuid import UUID

from fastapi import HTTPException

from backend.app.db.repositories.metric_repository import MetricRepository
from backend.app.schemas.metrics import MetricCreate, MetricDefinition, MetricUpdate


class MetricService:
    def __init__(self, repository: MetricRepository | None = None) -> None:
        self.repository = repository or MetricRepository()

    def list_metrics(self) -> list[MetricDefinition]:
        return self.repository.list()

    def get_metric(self, metric_id: UUID) -> MetricDefinition:
        metric = self.repository.get(metric_id)
        if metric is None:
            raise HTTPException(status_code=404, detail="指标不存在")
        return metric

    def create_metric(self, payload: MetricCreate) -> MetricDefinition:
        return self.repository.create(payload)

    def update_metric(self, metric_id: UUID, payload: MetricUpdate) -> MetricDefinition:
        metric = self.repository.update(metric_id, payload)
        if metric is None:
            raise HTTPException(status_code=404, detail="指标不存在")
        return metric

    def delete_metric(self, metric_id: UUID) -> dict[str, bool]:
        deleted = self.repository.delete(metric_id)
        if not deleted:
            raise HTTPException(status_code=404, detail="指标不存在")
        return {"deleted": True}
