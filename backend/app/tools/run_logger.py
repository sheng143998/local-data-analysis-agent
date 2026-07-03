from uuid import UUID, uuid4

from backend.app.db.repositories.run_repository import RunRepository
from backend.app.schemas.runs import QueryRunCreate, QueryRunRecord, ToolCallCreate, ToolCallRecord


class QueryRunLogger:
    """记录 Agent 运行和工具调用的最小落库工具。"""

    def __init__(self, repository: RunRepository | None = None) -> None:
        self.repository = repository or RunRepository()

    def log_run(
        self,
        *,
        user_question: str,
        generated_sql: str | None,
        final_sql: str | None,
        guard_status: str,
        execution_status: str,
        row_count: int,
        latency_ms: int,
        memory_hit: bool = False,
        memory_id: UUID | None = None,
        error_message: str | None = None,
    ) -> QueryRunRecord:
        return self.repository.create_run(
            QueryRunCreate(
                id=uuid4(),
                user_question=user_question,
                memory_hit=memory_hit,
                memory_id=memory_id,
                generated_sql=generated_sql,
                final_sql=final_sql,
                guard_status=guard_status,
                execution_status=execution_status,
                row_count=row_count,
                latency_ms=latency_ms,
                error_message=error_message,
            )
        )

    def log_tool_call(
        self,
        *,
        query_run_id: UUID,
        tool_name: str,
        input_payload: dict,
        output_payload: dict,
        status: str,
        latency_ms: int = 0,
        error_message: str | None = None,
    ) -> ToolCallRecord:
        return self.repository.create_tool_call(
            ToolCallCreate(
                id=uuid4(),
                query_run_id=query_run_id,
                tool_name=tool_name,
                input_payload=input_payload,
                output_payload=output_payload,
                status=status,
                latency_ms=latency_ms,
                error_message=error_message,
            )
        )
