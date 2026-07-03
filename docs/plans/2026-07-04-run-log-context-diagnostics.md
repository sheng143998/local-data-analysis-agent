# 运行日志上下文诊断增强计划

## Goal

当前 `/api/runs/{run_id}` 能看到工具调用摘要，但上下文召回、SQL 生成和 Guard 的输出还不够利于诊断。标准评估失败时，开发者需要知道本次召回了多少表关系、SQL 生成有哪些 warning、Guard 报了哪些错误或 warning。本模块增强 `tool_calls.output_payload`，不改普通用户界面，不新增固定 SQL 模板。

## Current task

当前正在做：本模块已完成实现、测试、文档更新、commit 和 push。

## Scope

包含：

- context builder 工具调用增加：
  - `metric_count`
  - `schema_column_count`
  - `relationship_count`
  - `tables`
  - `fields_sample`
- SQL generation 工具调用增加：
  - `generation_path`
  - `warning_count`
  - `warnings`
  - `has_sql`
- Guard 工具调用增加：
  - `guard_status`
  - `warning_count`
  - `warnings`
  - `error_count`
  - `errors`
- 更新 runs 测试和文档。

不包含：

- 不改数据库表结构。
- 不改变普通用户前端。
- 不记录完整 prompt、模型原始输出或完整结果集。
- 不新增固定 SQL 模板。

## Module boundary

上游输入：

- `RetrievalContext`
- `GeneratedSql`
- `SqlGuardResult`

下游输出：

- `tool_calls.output_payload`
- `/api/runs/{run_id}` 开发者调试响应

预计触达文件：

- `backend/app/agents/analysis_graph.py`
- `backend/tests/test_runs.py`
- `docs/agent_workflow.md`
- `docs/api.md`
- `docs/handoff/current.md`
- `docs/modules/2026-07-04-run-log-context-diagnostics.md`

## Business logic

开发者查看单次运行详情时，可以快速判断：

- schema/metric 召回是否足够；
- 表关系上下文是否生成；
- SQL 生成是否有模型或 fallback warning；
- Guard 是因为字段、表、写操作还是其他原因拦截。

普通业务用户仍然只看到分析结果、SQL、表格和来源，不看到这些内部诊断 payload。

## Data contract

数据库结构不变，`tool_calls.output_payload` 增加 JSON 字段。

## Implementation steps

- [x] 读取 handoff、run logger、runs 测试、analysis graph 和相关文档。
- [x] 创建计划文档。
- [x] 增强 analysis graph 日志 payload。
- [x] 更新 runs focused tests。
- [x] 更新文档、handoff 和模块完成说明。
- [x] 运行验证。
- [x] commit 并 push。

## Validation plan

- `py -3 -m pytest backend/tests/test_runs.py`
- `npm run backend:test`
- `npm run eval:standard`
- `npm run frontend:build`
- `npm run test:e2e`

## Risks and open questions

- 诊断 payload 可能变大，所以只记录字段样例和 warning/error 摘要，不记录完整 prompt 或完整结果集。
- `/api/runs` 仍是开发者接口，后续上线前需要鉴权。
