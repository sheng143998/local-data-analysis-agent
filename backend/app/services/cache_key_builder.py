"""查询结果缓存 Key 构造器。

业务目的：缓存 Key 必须绑定 SQL、Query Plan、用户权限范围和语义/schema
版本，避免不同口径或不同权限用户读到彼此的结果。
"""
from __future__ import annotations

import hashlib
import json
from typing import Any

from backend.app.core.config import settings


def build_query_cache_key(
    *,
    final_sql: str,
    query_plan: dict[str, Any] | None = None,
    app_user_id: Any = None,
    resolved_contracts: list[dict[str, Any]] | None = None,
    schema_version: str | None = None,
) -> str:
    """生成稳定的查询结果缓存 Key。

    参数：
      final_sql: Guard 放行后的最终 SQL。
      query_plan: 结构化 Query Plan，用于区分不同指标/维度/过滤口径。
      app_user_id: 当前用户 ID；开发模式为 development principal。
      resolved_contracts: 已绑定的语义合同列表，用于感知合同版本变化。
      schema_version: schema 版本；缺省使用配置中的 QUERY_CACHE_SCHEMA_VERSION。
    """
    effective_schema_version = schema_version or settings.query_cache_schema_version
    permission_hash = _stable_hash(str(app_user_id or "development"))
    plan_hash = _stable_hash(json.dumps(query_plan or {}, ensure_ascii=False, sort_keys=True))
    contract_hash = _stable_hash(
        json.dumps(_normalize_contracts(resolved_contracts or []), ensure_ascii=False, sort_keys=True)
    )
    sql_hash = _stable_hash(final_sql.strip())
    digest = hashlib.sha256(
        ":".join(
            [
                effective_schema_version,
                permission_hash,
                plan_hash,
                contract_hash,
                sql_hash,
            ]
        ).encode("utf-8")
    ).hexdigest()
    return f"{settings.query_cache_prefix}:v1:{digest}"


def _normalize_contracts(contracts: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """只保留合同身份字段，避免无关诊断字段污染 Key。"""
    normalized: list[dict[str, Any]] = []
    for contract in contracts:
        item = {
            "contract_key": contract.get("contract_key") or contract.get("key"),
            "version": contract.get("version"),
        }
        if item["contract_key"] is not None or item["version"] is not None:
            normalized.append(item)
    return sorted(normalized, key=lambda item: (str(item.get("contract_key")), str(item.get("version"))))


def _stable_hash(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()[:16]
