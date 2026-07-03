import json
import re
from typing import Any

from backend.app.core.model_adapter import ModelAdapter, ModelMessage, ModelRequest, ModelResponse
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
) -> GeneratedSql:
    """通过统一 ModelAdapter 生成 SQL 文本，但不执行 SQL。"""
    model_adapter = adapter or ModelAdapter()
    messages = build_sql_generation_messages(question, retrieval_context, reuse_plan)
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
    path = "model_rewrite" if reuse_plan.path_type == "rewrite_path" else "model_generate"
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
) -> list[ModelMessage]:
    return [
        ModelMessage(role="system", content=_system_prompt()),
        ModelMessage(
            role="user",
            content=_user_prompt(question, retrieval_context, reuse_plan),
        ),
    ]


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
) -> str:
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
        "requirements": [
            "只能使用 allowed_tables 和 schema_fields 中出现的字段",
            "跨表查询优先使用 table_relationships 中的高置信关系",
            "不要编造表名、字段名或业务口径",
            "输出 SQL 后还会经过 Validator 和 Guard",
        ],
    }
    return json.dumps(payload, ensure_ascii=False, indent=2)


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
