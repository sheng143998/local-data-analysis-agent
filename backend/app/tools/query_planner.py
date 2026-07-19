from backend.app.schemas.query_plan import QueryContractConstraint, QueryExecutionContract, QueryMeasure, QueryPlan
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
    filters = list(dict.fromkeys([*(_business_filters(intent.filters)), *contract_plan["filters"]]))
    execution_contract = _build_execution_contract(intent, entities, measures, dimensions, filters)
    # 业务规则：已支付订单是一个规范支付谓词，不能同时把自然语言短语当作第二个 SQL 过滤条件。
    filters = execution_contract.canonical_filters
    expected_columns = list(
        dict.fromkeys(
            [
                *contract_plan["expected_columns"],
                *(measure.name for measure in measures),
                *(execution_contract.output_aliases.values()),
            ]
        )
    )
    expected_row_shape = contract_plan["expected_row_shape"] or ("ranking" if spec.top_n else "grouped" if dimensions else "single")
    return QueryPlan(
        entities=entities,
        measures=measures,
        dimensions=dimensions,
        # 业务规则：契约声明的默认过滤器只进入结构化计划，仍由模型、Inspector、Guard 和 Executor 共同校验。
        filters=filters,
        time_filter=execution_contract.time_predicate or spec.time_filter,
        order_by=contract_plan["order_by"] or (dimensions if spec.requires_order_by else []),
        limit=spec.top_n or contract_plan["limit"],
        expected_columns=expected_columns,
        expected_row_shape=expected_row_shape,
        contract_keys=[str(contract.get("contract_key")) for contract in contracts if contract.get("contract_key")],
        contract_constraints=_contract_constraints(contracts),
        execution_contract=execution_contract,
    )


def _contract_constraints(contracts: list[dict]) -> list[QueryContractConstraint]:
    """业务规则：只把已审核契约的来源和聚合约束交给 SQL，不生成固定 SQL。"""
    constraints: list[QueryContractConstraint] = []
    for contract in contracts:
        key = str(contract.get("contract_key") or "").strip()
        if not key:
            continue
        constraints.append(
            QueryContractConstraint(
                contract_key=key,
                display_name=str(contract.get("display_name") or ""),
                aggregation=str(contract.get("aggregation") or ""),
                source_tables=[str(table) for table in contract.get("source_tables", []) if table],
                source_fields=[str(field) for field in contract.get("source_fields", []) if field],
            )
        )
    return constraints


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
    """业务规则：把模型中文候选统一为 QuerySpec 技术维度，避免重复分组和别名误判。"""
    dimensions = [_canonical_dimension(dimension) for dimension in dimensions]
    aliases = {
        "payment_method": "payment_type",
        "按天": "date",
        "每天": "date",
        "日期": "date",
        "按月": "month",
        "每月": "month",
        "月份": "month",
        "月度": "month",
        "品类": "category",
        "城市": "city",
        "州": "state",
        "支付方式": "payment_type",
        "流量来源": "source",
        "优惠券": "coupon",
    }
    return list(dict.fromkeys(aliases.get(str(dimension), str(dimension)) for dimension in dimensions if dimension))


def _canonical_dimension(value: str) -> str:
    return "category" if str(value) in {"商品品类", "类目", "分类", "category"} else str(value)


def _operation(metric: str) -> str:
    if metric.endswith("_rate") or metric.endswith("_margin"):
        return "ratio"
    if metric.startswith("avg_"):
        return "average"
    if metric.endswith("_count"):
        return "count"
    return "sum"


def _business_filters(filters: list[str]) -> list[str]:
    """业务规则：排行、Top N 与时间粒度属于 Query Plan 结构，绝不能作为 WHERE 过滤传给 Inspector。"""
    structural = ("前", "top", "最高", "最低", "最多", "最少", "排行", "排名", "按月", "按天", "趋势", "分布")
    return [item for item in filters if item and not any(token in str(item).lower() for token in structural)]


def _build_execution_contract(
    intent: ParsedQuestionIntent,
    entities: list[str],
    measures: list[QueryMeasure],
    dimensions: list[str],
    filters: list[str],
) -> QueryExecutionContract:
    """把已确认的业务意图收敛为模型可直接映射的查询约束，不生成 SQL。"""
    metric_names = {measure.name for measure in measures}
    has_paid_filter = any("payments.status = 'paid'" in item.lower() for item in filters)
    paid_order_scope = (
        "orders" in entities
        and "payments" in entities
        and bool(metric_names & {"sales_amount", "order_count", "avg_order_value"})
        and any(token in intent.original_question for token in ("已支付", "支付成功", "已付款", "成交"))
    )
    if has_paid_filter and "orders" in entities and "payments" in entities:
        paid_order_scope = True
    time_field = _time_field(intent, entities)
    time_predicate = intent.query_spec.time_filter.replace("{time_field}", time_field) if time_field else ""
    canonical_filters = [item for item in filters if not _is_paid_order_filter(item)]
    if paid_order_scope:
        canonical_filters.append("payments.status = 'paid'")
    canonical_filters = list(dict.fromkeys(canonical_filters))

    join_strategy: list[str] = []
    aggregation_grain = ""
    if paid_order_scope:
        join_strategy = [
            "先从 payments 中按 payments.order_id 去重筛选 payments.status = 'paid' 的订单。",
            "再以已支付订单的 order_id 与 orders.id 关联；不得直接在多条 payments 关联结果上汇总 orders.total_amount。",
        ]
        aggregation_grain = "order"
    elif metric_names & {"sales_amount", "order_count", "avg_order_value"}:
        aggregation_grain = "order"

    output_aliases = _output_aliases(metric_names, dimensions)
    group_expression = ""
    if time_field and "month" in dimensions:
        group_expression = f"DATE_TRUNC('month', {time_field})"
    elif time_field and "date" in dimensions:
        group_expression = f"DATE_TRUNC('day', {time_field})"

    return QueryExecutionContract(
        time_field=time_field,
        time_predicate=time_predicate,
        time_group_expression=group_expression,
        canonical_filters=canonical_filters,
        join_strategy=join_strategy,
        aggregation_grain=aggregation_grain,
        output_aliases=output_aliases,
    )


def _time_field(intent: ParsedQuestionIntent, entities: list[str]) -> str:
    if not intent.query_spec.time_filter:
        return ""
    if "orders" in entities:
        return "orders.purchase_at"
    if "payments" in entities:
        return "payments.paid_at"
    if "refunds" in entities:
        return "refunds.created_at"
    if "traffic_events" in entities:
        return "traffic_events.created_at"
    if "users" in entities:
        return "users.created_at"
    return ""


def _output_aliases(metric_names: set[str], dimensions: list[str]) -> dict[str, str]:
    aliases: dict[str, str] = {}
    for dimension in dimensions:
        aliases[dimension] = {"payment_type": "payment_method"}.get(dimension, dimension)
    for metric in metric_names:
        aliases[metric] = metric
    return aliases


def _is_paid_order_filter(value: str) -> bool:
    text = str(value).strip().lower()
    return text in {"已支付", "支付成功", "已付款", "成交", "已支付订单", "支付成功订单", "已付款订单", "成交订单"}
