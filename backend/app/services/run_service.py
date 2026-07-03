from uuid import UUID

from fastapi import HTTPException

from backend.app.db.repositories.run_repository import RunRepository
from backend.app.schemas.runs import QueryRunDetail, QueryRunRecord


class RunService:
    def __init__(self, repository: RunRepository | None = None) -> None:
        self.repository = repository or RunRepository()

    def list_runs(self, limit: int = 20) -> list[QueryRunRecord]:
        safe_limit = min(max(limit, 1), 100)
        return self.repository.list_runs(safe_limit)

    def get_run(self, run_id: UUID) -> QueryRunDetail:
        run = self.repository.get_run(run_id)
        if run is None:
            raise HTTPException(status_code=404, detail="运行记录不存在")
        return run
