# 评估 Run Trace 摘要诊断计划

## Goal

让标准评估报告不仅能链接到 `/api/runs/{run_id}`，还直接携带关键运行摘要，帮助判断断言失败是 schema 召回不足、SQL 生成不足，还是 Guard/执行问题。

## Current Task

当前正在做：模块已完成、已提交并推送。

## Scope

- 包含：评估脚本、评估 runner 测试、评估文档、README、handoff 和模块说明。
- 不包含：普通用户前端展示评估报告；新增固定 SQL 模板；改变 `/api/analyze` 响应；改变数据库结构。

## Module Boundary

- 上游输入：`/api/analyze` 响应、开发者 `/api/runs/{run_id}` 详情。
- 内部处理：eval runner 提取 context、generation、guard、memory 工具调用摘要。
- 下游输出：`eval/reports/latest_eval_report.json` 的 `cases[]`、`assertion_failures[]` 和 `assertion_failure_summary`。

## Business Logic

开发者跑标准评估后，可以直接看到失败 case 的上下文召回表、字段样例、SQL 生成路径、Guard warning/error 等摘要。如果期望表没有进入 `context_tables`，优先修 schema/metric 检索；如果进入了上下文但 SQL 没用上，优先修 SQL 生成或复用策略。

## Data Contract

- `EvalCaseResult.run_trace_summary`: dict，包含：
  - `context_tables`
  - `context_fields_sample`
  - `relationship_count`
  - `generation_path`
  - `generation_warnings`
  - `guard_status`
  - `guard_errors`
  - `memory_path_type`
- `assertion_failure_summary.by_missing_table_context_status`: 聚合缺失表是否出现在 run context 中。

## Implementation Steps

任务清单：
- [x] 创建模块计划文档。
- [x] 实现 run detail 摘要提取。
- [x] 增加 focused tests。
- [x] 更新文档。
- [x] 运行完整验证。
- [x] 更新 handoff、提交并推送。

## Validation Plan

- `py -3 -m pytest backend/tests/test_eval_runner.py`
- `npm run backend:test`
- `npm run eval:standard`
- `npm run frontend:build`
- `npm run test:e2e`

## Risks And Open Questions

- 当前摘要依赖工具调用名称稳定；如果后续重命名工具，需要同步调整 eval runner。
- 摘要只保留样例和诊断字段，不记录完整 prompt 或完整结果集。
