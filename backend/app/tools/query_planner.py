from backend.app.schemas.query_plan import QueryMeasure, QueryPlan
from backend.app.tools.question_intent_parser import ParsedQuestionIntent


def build_query_plan(intent: ParsedQuestionIntent) -> QueryPlan:
    """把已确认的意图转换为生成约束，未知概念不在此处猜测 SQL 公式。"""
    spec = intent.query_spec
    contracts = intent.resolved_contracts
    entities = sorted({table for contract in contracts for table in contract.get("source_tables", [])} | set(spec.required_tables))
    measures = [QueryMeasure(name=name, operation=_operation(name)) for name in spec.metrics]
    if not measures:
        measures = [QueryMeasure(name=name) for name in intent.semantic_metrics]
    dimensions = list(dict.fromkeys(spec.dimensions or intent.semantic_dimensions))
    expected_columns = [measure.name for measure in measures] + dimensions
    return QueryPlan(
        entities=entities,
        measures=measures,
        dimensions=dimensions,
        filters=list(intent.filters),
        time_filter=spec.time_filter,
        order_by=dimensions if spec.requires_order_by else [],
        limit=spec.top_n,
        expected_columns=expected_columns,
        expected_row_shape="ranking" if spec.top_n else "grouped" if dimensions else "single",
        contract_keys=[str(contract.get("contract_key")) for contract in contracts if contract.get("contract_key")],
    )


def _operation(metric: str) -> str:
    if metric.endswith("_rate") or metric.endswith("_margin"):
        return "ratio"
    if metric.startswith("avg_"):
        return "average"
    if metric.endswith("_count"):
        return "count"
    return "sum"
