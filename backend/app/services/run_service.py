from uuid import UUID
from typing import Any

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
        return run.model_copy(update={"debug_summary": _build_debug_summary(run)})


def _build_debug_summary(run: QueryRunDetail) -> dict[str, Any]:
    tools = {tool.tool_name: tool for tool in run.tool_calls}
    generation = _output_payload(tools, "analysis_graph.select_generated_sql")
    guard = _output_payload(tools, "sql_validation_tools.guard_sql")
    execution = _output_payload(tools, "sql_execution_tools.execute_guarded_sql")
    memory_plan = _output_payload(tools, "sql_memory_tools.plan_sql_reuse")
    context = _output_payload(tools, "context_builder.build_retrieval_context")
    timings = _output_payload(tools, "analysis_graph.pipeline_timings")
    intent_verification = generation.get("intent_verification")
    if not isinstance(intent_verification, dict):
        intent_verification = {}
    return {
        "run": {
            "id": str(run.id),
            "question": run.user_question,
            "rewritten_question": run.rewritten_question,
            "guard_status": run.guard_status,
            "execution_status": run.execution_status,
            "row_count": run.row_count,
            "latency_ms": run.latency_ms,
            "memory_hit": run.memory_hit,
        },
        "memory": {
            "path_type": str(memory_plan.get("path_type") or ""),
            "reuse_type": str(memory_plan.get("reuse_type") or ""),
            "score": memory_plan.get("score"),
        },
        "context": {
            "metric_count": _safe_int(context.get("metric_count")),
            "schema_column_count": _safe_int(context.get("schema_column_count")),
            "relationship_count": _safe_int(context.get("relationship_count")),
            "tables": _string_list(context.get("tables")),
            "fields_sample": _string_list(context.get("fields_sample")),
        },
        "sql_generation": {
            "path": str(generation.get("generation_path") or ""),
            "has_sql": bool(generation.get("has_sql")),
            "warning_count": _safe_int(generation.get("warning_count")),
            "warnings": _string_list(generation.get("warnings")),
            "context_table_coverage": generation.get("context_table_coverage") or {},
        },
        "intent_validation": {
            "decision": str(intent_verification.get("decision") or ""),
            "warning_count": _safe_int(intent_verification.get("warning_count")),
            "warnings": _string_list(intent_verification.get("warnings")),
            "repair_attempts": _safe_int(intent_verification.get("repair_attempts")),
        },
        "guard": {
            "status": str(guard.get("guard_status") or ""),
            "warning_count": _safe_int(guard.get("warning_count")),
            "warnings": _string_list(guard.get("warnings")),
            "error_count": _safe_int(guard.get("error_count")),
            "errors": _string_list(guard.get("errors")),
        },
        "execution": {
            "status": str(execution.get("execution_status") or run.execution_status),
            "row_count": _safe_int(execution.get("row_count")),
        },
        "timings": {
            "node_timings_ms": timings.get("node_timings_ms")
            if isinstance(timings.get("node_timings_ms"), dict)
            else {},
            "total_latency_ms": _safe_int(timings.get("total_latency_ms") or run.latency_ms),
            "slowest_node": timings.get("slowest_node")
            if isinstance(timings.get("slowest_node"), dict)
            else {},
        },
    }


def _output_payload(tools: dict[str, Any], tool_name: str) -> dict[str, Any]:
    tool = tools.get(tool_name)
    if tool is None:
        return {}
    return tool.output_payload if isinstance(tool.output_payload, dict) else {}


def _string_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item) for item in value if item is not None]


def _safe_int(value: Any) -> int:
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return 0
