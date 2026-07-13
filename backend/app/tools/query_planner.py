from backend.app.schemas.query_plan import QueryMeasure, QueryPlan
from backend.app.tools.question_intent_parser import ParsedQuestionIntent


def build_query_plan(intent: ParsedQuestionIntent) -> QueryPlan:
    """把已确认的意图转换为生成约束，未知概念不在此处猜测 SQL 公式。"""
    spec = intent.query_spec
    contracts = intent.resolved_contracts
    entities = sorted({table for contract in contracts for table in contract.get("source_tables", [])} | set(spec.required_tables))
    contract_plan = _merge_contract_plan(contracts)
    measures = [QueryMeasure(name=name, operation=_operation(name)) for name in spec.metrics]
    if not measures:
        measures = [QueryMeasure(name=name) for name in intent.semantic_metrics]
    if contract_plan["measures"]:
        measures = [*measures, *contract_plan["measures"]]
    measures = _unique_measures(measures)
    dimensions = _merge_dimensions(
        [*spec.dimensions, *intent.semantic_dimensions, *contract_plan["dimensions"]]
    )
    expected_columns = list(dict.fromkeys([*contract_plan["expected_columns"], *(measure.name for measure in measures), *dimensions]))
    expected_row_shape = contract_plan["expected_row_shape"] or ("ranking" if spec.top_n else "grouped" if dimensions else "single")
    return QueryPlan(
        entities=entities,
        measures=measures,
        dimensions=dimensions,
        # 业务规则：契约声明的默认过滤器只进入结构化计划，仍由模型、Inspector、Guard 和 Executor 共同校验。
        filters=list(dict.fromkeys([*intent.filters, *contract_plan["filters"]])),
        time_filter=spec.time_filter,
        order_by=contract_plan["order_by"] or (dimensions if spec.requires_order_by else []),
        limit=spec.top_n or contract_plan["limit"],
        expected_columns=expected_columns,
        expected_row_shape=expected_row_shape,
        contract_keys=[str(contract.get("contract_key")) for contract in contracts if contract.get("contract_key")],
    )


def _merge_contract_plan(contracts: list[dict]) -> dict:
    """仅把已解析契约的声明性查询形态合并进计划，不生成或执行 SQL。"""
    merged = {
        "measures": [],
        "dimensions": [],
        "filters": [],
        "order_by": [],
        "limit": None,
        "expected_columns": [],
        "expected_row_shape": "",
    }
    for contract in contracts:
        plan = contract.get("semantic_config", {}).get("plan", {})
        if not isinstance(plan, dict):
            continue
        for measure in plan.get("measures", []):
            if isinstance(measure, dict) and measure.get("name"):
                merged["measures"].append(QueryMeasure(**measure))
        for key in ("dimensions", "filters", "order_by", "expected_columns"):
            merged[key].extend(str(value) for value in plan.get(key, []) if value)
        if not merged["limit"] and isinstance(plan.get("limit"), int):
            merged["limit"] = plan["limit"]
        if not merged["expected_row_shape"] and plan.get("expected_row_shape"):
            merged["expected_row_shape"] = str(plan["expected_row_shape"])
    merged["measures"] = _unique_measures(merged["measures"])
    for key in ("dimensions", "filters", "order_by", "expected_columns"):
        merged[key] = list(dict.fromkeys(merged[key]))
    return merged


def _unique_measures(measures: list[QueryMeasure]) -> list[QueryMeasure]:
    unique: dict[str, QueryMeasure] = {}
    for measure in measures:
        unique[measure.name] = measure
    return list(unique.values())


def _merge_dimensions(dimensions: list[str]) -> list[str]:
    """业务规则：支付方式的展示别名统一回 QuerySpec 的 payment_type 维度 ID，避免重复分组。"""
    aliases = {"payment_method": "payment_type"}
    return list(dict.fromkeys(aliases.get(str(dimension), str(dimension)) for dimension in dimensions if dimension))


def _operation(metric: str) -> str:
    if metric.endswith("_rate") or metric.endswith("_margin"):
        return "ratio"
    if metric.startswith("avg_"):
        return "average"
    if metric.endswith("_count"):
        return "count"
    return "sum"
