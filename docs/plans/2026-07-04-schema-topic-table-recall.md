# Schema 主题表召回增强计划

## Goal

增强 schema retriever 对用户、流量、优惠券等业务主题的表召回能力，让标准评估中缺失的 `users`、`traffic_events`、`coupons`、`coupon_usages` 更容易进入 `RetrievalContext`，为后续通用 SQL 生成打基础。

## Current Task

当前正在做：模块已完成、已提交并推送。

## Scope

- 包含：schema 表召回规则、检索测试、README/评估文档/Agent 工作流文档、handoff 和模块说明。
- 不包含：新增固定 SQL 模板；改变 `/api/analyze` 响应；改变普通用户前端；改变数据库结构。

## Module Boundary

- 上游输入：用户自然语言问题和已召回指标口径。
- 内部处理：`schema_retriever._related_tables()` 根据业务词把相关表加入 schema 读取范围。
- 下游输出：`retrieve_schema()` 返回的 `SchemaColumnContext`，再进入 `RetrievalContext.tables/fields/table_relationships` 和模型 SQL prompt。

## Business Logic

当用户问“访问转化率、流量来源、优惠券核销率、新增用户数”等问题时，系统应先把相关业务表字段召回到上下文，而不是只围绕订单、支付、退款表。这样后续模型 SQL 生成或更通用生成策略才有足够真实字段可用。

## Data Contract

- API 响应不变。
- 数据库结构不变。
- 后端内部 `RetrievalContext.tables` 和 `fields` 可能新增更多相关表字段。

## Implementation Steps

任务清单：
- [x] 创建模块计划文档。
- [x] 实现主题表召回规则。
- [x] 增加 focused tests。
- [x] 更新文档。
- [x] 运行完整验证。
- [x] 更新 handoff、提交并推送。

## Validation Plan

- `py -3 -m pytest backend/tests/test_retrieval_tools.py`
- `npm run backend:test`
- `npm run eval:standard`
- `npm run frontend:build`
- `npm run test:e2e`

## Risks And Open Questions

- 本模块只确保相关表进入上下文，不保证当前确定性 SQL 生成会使用它们。
- 后续仍需结合 `run_trace_summary` 判断 SQL Memory 或生成策略是否绕过了已召回上下文。
