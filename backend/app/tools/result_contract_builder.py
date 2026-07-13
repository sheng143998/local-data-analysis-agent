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
        # 业务上 0 值聚合仍有一行结果，只有成功且零行才是空结果。
        result_state="empty" if execution.status == "success" and execution.row_count == 0 else execution.status,
        time_range=str(plan.get("time_filter") or ""),
        warnings=warnings,
    )
