from backend.app.schemas.result_contract import ResultColumn, ResultContract
from backend.app.schemas.sql_execution import SqlExecutionResult


def build_result_contract(question: str, execution: SqlExecutionResult, query_plan: dict | None, warnings: list[str]) -> ResultContract:
    plan = query_plan or {}
    measures = {item.get("name") for item in plan.get("measures", []) if isinstance(item, dict)}
    dimensions = set(plan.get("dimensions", []))
    return ResultContract(
        resolved_question=question,
        query_plan=plan,
        columns=[ResultColumn(name=column, semantic_role="metric" if column in measures else "dimension" if column in dimensions else "unknown") for column in execution.columns],
        rows=execution.rows,
        row_count=execution.row_count,
        time_range=str(plan.get("time_filter") or ""),
        warnings=warnings,
    )
