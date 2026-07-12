# 模型优先订单数 Fallback 计划

## Goal

将单一订单数 SQL 从“直接跳过模型的硬模板”改为“模型优先、一次 Repair 后的受控恢复策略”。

## Scope

- 保留模型 SQL 生成和一次 Repair 作为订单数问题的默认路径。
- 仅在模型未返回 SQL，或修复后仍无法满足 QuerySpec 时，对无维度、无排行的 `order_count` 启用已支付口径 fallback。
- 保留意图校验、SQL Guard 和只读 Executor。
- 更新单元测试、模块记录和 handoff。

## Out of scope

- 不将 fallback 扩展为任意指标或复杂维度问题的通用模板。
- 不增加模型重试次数或放宽 Guard/支付口径。

## Implementation steps

- [x] 从 SQL 生成入口移除订单数直接 fallback。
- [x] 在模型无 SQL 或一次 Repair 失败后的意图校验节点注入受控 fallback。
- [x] 覆盖模型优先、修复失败 fallback 和 Guard 入口测试。
- [x] 执行 focused pytest、后端全量测试和标准评测。
- [x] 记录完成状态并提交推送。

## Validation plan

- `py -3 -m pytest backend/tests/test_analysis_graph_sql_selection.py`
- `npm.cmd run backend:test`
- `npm.cmd run eval:standard`

## Risks

- 模型优先会使简单订单数请求的平均延迟高于直接 fallback；这是保留模型泛化能力的明确代价。
- 小模型仍可能生成失败，最终 fallback 仅保障已定义且语义明确的单指标订单数。
