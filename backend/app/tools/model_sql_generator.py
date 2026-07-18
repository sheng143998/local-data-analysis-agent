import json
import re
from typing import Any

from backend.app.core.model_adapter import ModelAdapter, ModelAdapterConfig, ModelMessage, ModelRequest, ModelResponse
from backend.app.core.model_routing import route_model
from backend.app.schemas.memories import SqlReusePlan
from backend.app.schemas.retrieval import RetrievalContext
from backend.app.schemas.sql_generation import GeneratedSql


SQL_JSON_RESPONSE_FORMAT = {"type": "json_object"}
MAX_SCHEMA_FIELDS_IN_PROMPT = 80


def generate_sql_with_model(
    question: str,
    retrieval_context: RetrievalContext,
    reuse_plan: SqlReusePlan,
    adapter: ModelAdapter | None = None,
    repair_context: dict[str, Any] | None = None,
    question_intent: dict[str, Any] | None = None,
) -> GeneratedSql:
    """通过统一 ModelAdapter 生成 SQL 文本，但不执行 SQL。"""
    route = route_model("sql_repair" if repair_context else "sql_generation")
    model_adapter = adapter or ModelAdapter(
        ModelAdapterConfig(
            provider=route.provider,
            base_url=route.base_url,
            model=route.model,
        )
    )
    messages = build_sql_generation_messages(
        question,
        retrieval_context,
        reuse_plan,
        repair_context,
        question_intent=question_intent,
    )
    response = model_adapter.chat(
        ModelRequest(
            messages=messages,
            temperature=0,
            max_tokens=1200,
            response_format=SQL_JSON_RESPONSE_FORMAT,
        )
    )
    if not response.ok:
        return GeneratedSql(
            path="model_error",
            warnings=[response.error_message or "模型 SQL 生成失败"],
            model_provider=response.provider,
            model_name=response.model,
            model_latency_ms=response.latency_ms,
        )

    parsed = parse_model_sql_response(response)
    path = (
        "model_repair"
        if repair_context
        else "model_rewrite" if reuse_plan.path_type == "rewrite_path"
        else "model_generate"
    )
    return GeneratedSql(
        path=path,
        sql=parsed["sql"],
        warnings=parsed["warnings"],
        model_provider=response.provider,
        model_name=response.model,
        model_latency_ms=response.latency_ms,
    )


def build_sql_generation_messages(
    question: str,
    retrieval_context: RetrievalContext,
    reuse_plan: SqlReusePlan,
    repair_context: dict[str, Any] | None = None,
    question_intent: dict[str, Any] | None = None,
) -> list[ModelMessage]:
    return [
        ModelMessage(role="system", content=_system_prompt()),
        ModelMessage(
            role="user",
            content=_user_prompt(
                question,
                retrieval_context,
                reuse_plan,
                repair_context,
                question_intent=question_intent,
            ),
        ),
    ]


def build_sql_generation_payload(
    question: str,
    retrieval_context: RetrievalContext,
    reuse_plan: SqlReusePlan,
    repair_context: dict[str, Any] | None = None,
    question_intent: dict[str, Any] | None = None,
) -> dict[str, Any]:
    metrics = [
        {
            "metric_name": metric.metric_name,
            "display_name": metric.display_name,
            "description": metric.description,
            "formula": metric.formula,
            "required_tables": metric.required_tables,
            "required_fields": metric.required_fields,
        }
        for metric in retrieval_context.metrics
    ]
    fields = [
        {
            "table": column.table_name,
            "column": column.column_name,
            "type": column.data_type,
            "meaning": column.business_meaning or column.description,
        }
        for column in retrieval_context.schema_columns[:MAX_SCHEMA_FIELDS_IN_PROMPT]
    ]
    relationships = [
        {
            "left": f"{relationship.left_table}.{relationship.left_column}",
            "right": f"{relationship.right_table}.{relationship.right_column}",
            "type": relationship.relationship_type,
            "confidence": relationship.confidence,
            "reason": relationship.reason,
        }
        for relationship in retrieval_context.table_relationships
    ]
    payload = {
        "question": question,
        "question_intent": _compact_question_intent(question_intent),
        # 业务规则：Query Plan 是本次 SQL 生成的必需契约，召回上下文仅作为候选知识，避免模型被无关表带偏。
        "query_plan": _compact_query_plan(question_intent),
        "reuse_plan": {
            "path_type": reuse_plan.path_type,
            "reuse_type": reuse_plan.reuse_type,
            "selected_sql": reuse_plan.selected_sql,
        },
        "allowed_tables": retrieval_context.tables,
        "allowed_fields": retrieval_context.fields,
        "metrics": metrics,
        "schema_fields": fields,
        "table_relationships": relationships,
        "metric_semantics": {
            "sales_amount": {
                "meaning": "总销售额 / 一共卖了多少钱",
                "preferred_formula": "SUM(orders.total_amount)",
                "grain": "order",
                "notes": [
                    "orders.total_amount is already an order-level amount.",
                    "When joining payments, do not multiply order totals by payment rows.",
                ],
            },
            "order_count": {
                "meaning": "订单数",
                "preferred_formula": "COUNT(DISTINCT orders.id)",
                "grain": "order",
            },
            "avg_order_value": {
                "meaning": "客单价 / 平均每单卖了多少钱",
                "preferred_formula": "SUM(orders.total_amount) / NULLIF(COUNT(DISTINCT orders.id), 0)",
                "grain": "order",
                "notes": [
                    "Do not use AVG(payments.amount) for average order value.",
                    "If payments is joined, calculate on distinct orders or pre-aggregate payments by order_id first.",
                ],
            },
        },
        "requirements": [
            "以 query_plan 的 entities、measures、dimensions、filters、order_by、limit 和 expected_row_shape 为本次查询的必需约束",
            "query_plan.entities 中的表必须实际参与查询；allowed_tables 中未被计划要求的表只是候选上下文，不要仅因其存在而 JOIN",
            "每个 query_plan.measures 只计算一次，并使用稳定的输出别名；每个 query_plan.dimensions 必须与聚合粒度一致",
            "query_plan.contract_constraints 是已审核的业务口径：必须使用其中 source_tables/source_fields，并采用 aggregation 指定的聚合方式；无法满足时不要编造替代口径。",
            "排行必须同时选择维度和度量、按 query_plan.order_by 排序并遵守 query_plan.limit",
            "只能使用 allowed_tables 和 schema_fields 中出现的字段",
            "跨表查询优先使用 table_relationships 中的高置信关系",
            "不要编造表名、字段名或业务口径",
            "“当前”“目前”“总数”“累计”本身不表示时间范围、已支付或成功状态；除非用户明确给出时间或支付条件，否则不要自行添加日期或支付状态过滤。",
            "查询某个实体的总量时，应统计该实体表的主键去重数量；不要把用户、商品等实体总量改写为订单、支付或新增指标。",
            "Olist 订单状态 orders.status 没有 paid；已支付口径必须使用 payments.status = 'paid'，并通过 orders.id = payments.order_id 关联",
            "严禁生成 orders.status = 'paid'。只有用户明确要求已支付、支付成功或成交口径时才使用 payments.status = 'paid'；否则不要添加支付状态条件。",
            "跨表条件必须使用显式 JOIN；如果使用 payments.status 或 payments.amount，SQL 必须包含 JOIN payments ON payments.order_id = orders.id",
            "同时查询总销售额和平均销售额时，必须分别输出 sales_amount 和 avg_order_value，不能把二者混为一个指标",
            "如果 JOIN payments 后汇总 orders.total_amount，必须先按 orders.id 去重或先按 payments.order_id 聚合，避免一单多支付导致订单金额重复累计",
            "输出 SQL 后还会经过 Validator 和 Guard",
        ],
    }
    query_plan = payload["query_plan"]
    payload["generation_contract"] = {
        "required_entities": query_plan["entities"],
        "required_measures": query_plan["measures"],
        "required_dimensions": query_plan["dimensions"],
        "required_filters": query_plan["filters"],
        "required_output_columns": query_plan["expected_columns"],
        "expected_row_shape": query_plan["expected_row_shape"],
        "contract_constraints": query_plan["contract_constraints"],
        "optional_context_tables": [
            table for table in retrieval_context.tables if table not in query_plan["entities"]
        ],
    }
    time_filter = _intent_time_filter(question_intent)
    if time_filter:
        payload["time_constraint"] = {
            "required_predicate": time_filter,
            "rule": "必须使用完整半开区间；起点使用 >=，终点使用 <，不得只写 IS NOT NULL、EXTRACT 或单侧日期条件。",
        }
        payload["requirements"].append(
            f"当前问题有明确时间范围，SQL WHERE 必须包含：{time_filter}；将 {{time_field}} 替换为相关的已允许时间字段，优先 orders.created_at。"
        )
    if repair_context:
        payload["repair_context"] = repair_context
        repair_rules = _repair_rules(repair_context)
        payload["repair_rules"] = repair_rules
        payload["requirements"].extend(
            [
                "这是一次 SQL 修复请求，必须优先修复 repair_context.intent_errors 中列出的问题",
                "不要重复输出 repair_context.previous_sql 中已被判定不符合意图的错误写法",
                *repair_rules,
            ]
        )
    return payload


def parse_model_sql_response(response: ModelResponse) -> dict[str, Any]:
    payload = _loads_json_object(response.content)
    sql = str(payload.get("sql") or "").strip().strip(";")
    warnings = _string_list(payload.get("warnings"))
    if not sql:
        warnings.append("模型响应未包含 sql 字段")
    if "select *" in sql.lower():
        warnings.append("模型 SQL 包含 SELECT *，后续 Validator/Guard 会拦截")
    return {
        "sql": sql,
        "reasoning": str(payload.get("reasoning") or ""),
        "tables": _string_list(payload.get("tables")),
        "metrics": _string_list(payload.get("metrics")),
        "warnings": warnings,
    }


def _system_prompt() -> str:
    return "\n".join(
        [
            "你是本地数据分析 Agent 的 SQL Generator。",
            "只生成 PostgreSQL SELECT 查询。",
            "只能使用用户消息中列出的表和字段。",
            "禁止 SELECT *，禁止 DDL/DML，禁止多语句。",
            "SQL 必须显式选择字段，并尽量添加 LIMIT。",
            "只输出 JSON，不要输出 Markdown。",
            'JSON 格式：{"sql":"SELECT ...","reasoning":"...","tables":["..."],"metrics":["..."],"warnings":[]}',
        ]
    )


def _user_prompt(
    question: str,
    retrieval_context: RetrievalContext,
    reuse_plan: SqlReusePlan,
    repair_context: dict[str, Any] | None = None,
    question_intent: dict[str, Any] | None = None,
) -> str:
    payload = build_sql_generation_payload(
        question,
        retrieval_context,
        reuse_plan,
        repair_context,
        question_intent=question_intent,
    )
    return json.dumps(payload, ensure_ascii=False, indent=2)


def _compact_question_intent(question_intent: dict[str, Any] | None) -> dict[str, Any]:
    if not question_intent:
        return {}
    allowed_keys = {
        "original_question",
        "normalized_question",
        "metrics",
        "dimensions",
        "semantic_metrics",
        "semantic_dimensions",
        "filters",
        "time_range",
        "confidence",
        "needs_clarification",
        "source",
        "query_spec",
        "query_plan",
        "resolved_contracts",
    }
    return {key: question_intent[key] for key in allowed_keys if key in question_intent}


def _intent_time_filter(question_intent: dict[str, Any] | None) -> str:
    if not isinstance(question_intent, dict):
        return ""
    query_spec = question_intent.get("query_spec")
    if not isinstance(query_spec, dict):
        return ""
    return str(query_spec.get("time_filter") or "").strip()


def _repair_rules(repair_context: dict[str, Any]) -> list[str]:
    rules: list[str] = []
    rules.extend(_inspector_repair_rules(repair_context.get("inspector_issues")))
    guard_errors = repair_context.get("guard_error", {}).get("guard_errors", [])
    all_errors = [*repair_context.get("intent_errors", []), *guard_errors]
    text = " ".join(str(error) for error in all_errors)
    if "字段不存在或未在 schema_metadata 中登记" in text:
        rules.append(
            "不得引用 schema_fields 未登记的字段。若 ORDER BY 使用输出别名，该别名必须在同一 SELECT 中以 `表达式 AS 别名` 明确定义；否则在 ORDER BY 中使用原表达式。"
        )
    if "时间范围" in text:
        required = repair_context.get("required", {})
        time_filter = str(required.get("time_filter") or "").strip()
        if time_filter:
            rules.append(
                f"必须在 WHERE 中加入完整时间条件：{time_filter}；将 {{time_field}} 替换为相关的已允许时间字段。"
            )
    if "错误支付口径" in text or "orders.status 没有 paid" in text:
        rules.append(
            "不得使用 orders.status = 'paid'。如果用户未明确要求已支付或支付成功，删除支付状态过滤；如果明确要求，使用 payments.status = 'paid' 并以 payments.order_id = orders.id 关联。"
        )
    if not rules:
        rules.append("逐条修复 repair_context 中的错误后再输出完整 PostgreSQL SELECT 查询。")
    # 业务规则：同一条规则只传一次，减少小模型重复注意力消耗和互相矛盾的修复指令。
    return list(dict.fromkeys(rule for rule in rules if str(rule).strip()))


def _inspector_repair_rules(issues: Any) -> list[str]:
    """把 Inspector 类别转换为可复制指令；未知类别保持保守，不猜测业务公式。"""
    if not isinstance(issues, list):
        return []
    fallback = "根据 inspector issue 修复 SQL 的结构问题；不得猜测业务公式，修复后仍必须满足 QuerySpec、Guard 和只读执行边界。"
    rules: list[str] = []
    category_defaults = {
        "syntax": "只输出一条可解析的 PostgreSQL SELECT；检查括号、逗号、引号和表别名，不输出 Markdown、解释文字或多条语句。",
        "missing_table": "补齐 Query Plan 要求的实体表，并只使用允许的真实连接字段；不要因为召回上下文中存在其他表而额外 JOIN。",
        "missing_order": "排行查询必须选择排行维度和度量，并按 Query Plan 的排序表达式加入 ORDER BY；不能按任意字段排序。",
        "missing_limit": "补齐 Query Plan 要求的 LIMIT，并使用计划给定数量；不得超过 SQL Guard 的行数上限。",
        "time_range": "在 WHERE 中补齐完整半开时间区间，使用 >= 起点和 < 终点；将占位时间字段替换为允许的真实字段。",
        "missing_measure": "补齐 Query Plan 中缺失的度量，每个度量只计算一次并使用稳定输出别名。",
        "missing_dimension": "补齐 Query Plan 中缺失的维度，并让 SELECT 与 GROUP BY 保持相同粒度。",
        "missing_output": "补齐 Query Plan 要求的输出列和别名，不要用 SELECT *。",
        "invalid_order": "修正 ORDER BY 的字段和方向，使其与 Query Plan 精确一致；最高、最多、前 N 使用 DESC。",
        "invalid_limit": "把 LIMIT 改为 Query Plan 指定的精确数量，不要使用通用默认 LIMIT。",
        "missing_filter": "补齐 Query Plan 已确认的业务过滤，保持相同字段和值，不得改写业务状态口径。",
        "contract_source_field": "使用合同要求的实体字段完成指标计算，不能以其他表、字段或 COUNT(*) 替代已确认口径。",
        "contract_aggregation": "按合同要求使用正确聚合方式，并在最终 SELECT 中输出对应指标别名。",
    }
    for issue in issues:
        if isinstance(issue, dict):
            explicit = str(issue.get("repair_rule") or "").strip()
            category = str(issue.get("category") or "").strip()
        else:
            explicit = str(getattr(issue, "repair_rule", "") or "").strip()
            category = str(getattr(issue, "category", "") or "").strip()
        rules.append(explicit or category_defaults.get(category, fallback))
    return rules


def _loads_json_object(content: str) -> dict[str, Any]:
    text = content.strip()
    if not text:
        return {}
    try:
        value = json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", text, flags=re.DOTALL)
        if not match:
            return {}
        try:
            value = json.loads(match.group(0))
        except json.JSONDecodeError:
            return {}
    return value if isinstance(value, dict) else {}


def _string_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item) for item in value if item is not None]


def _compact_query_plan(question_intent: dict[str, Any] | None) -> dict[str, Any]:
    """只保留 SQL 生成需要的计划字段，避免把内部解析细节暴露给模型。"""
    if not isinstance(question_intent, dict):
        return {
            "entities": [],
            "measures": [],
            "dimensions": [],
            "filters": [],
            "time_filter": "",
            "order_by": [],
            "limit": None,
            "expected_columns": [],
            "expected_row_shape": "unknown",
            "contract_constraints": [],
        }
    raw = question_intent.get("query_plan")
    if not isinstance(raw, dict):
        raw = {}
    measures: list[dict[str, str]] = []
    for measure in raw.get("measures", []):
        if isinstance(measure, dict) and measure.get("name"):
            measures.append({"name": str(measure["name"]), "operation": str(measure.get("operation") or "")})
        elif measure:
            measures.append({"name": str(measure), "operation": ""})
    return {
        "entities": _string_list(raw.get("entities")),
        "measures": measures,
        "dimensions": _string_list(raw.get("dimensions")),
        "filters": _string_list(raw.get("filters")),
        "time_filter": str(raw.get("time_filter") or ""),
        "order_by": _string_list(raw.get("order_by")),
        "limit": raw.get("limit") if isinstance(raw.get("limit"), int) else None,
        "expected_columns": _string_list(raw.get("expected_columns")),
        "expected_row_shape": str(raw.get("expected_row_shape") or "unknown"),
        "contract_constraints": [
            {
                "contract_key": str(item.get("contract_key") or ""),
                "display_name": str(item.get("display_name") or ""),
                "aggregation": str(item.get("aggregation") or ""),
                "source_tables": _string_list(item.get("source_tables")),
                "source_fields": _string_list(item.get("source_fields")),
            }
            for item in raw.get("contract_constraints", [])
            if isinstance(item, dict) and item.get("contract_key")
        ],
    }
