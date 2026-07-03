# 评估报告 Run Trace 关联计划

## Goal

让标准评估报告中的每个 case 都能关联到后端 `query_runs` 运行记录，便于从严格断言失败直接跳转到 `/api/runs/{run_id}` 查看工具调用摘要。

## Current Task

当前正在做：模块已完成、已提交并推送。

## Scope

- 包含：评估脚本、评估测试、评估文档、README/handoff/module 文档。
- 不包含：普通用户前端展示 run trace；新增 SQL 模板；改变 `/api/analyze` 响应契约；改变 `query_runs` 表结构。

## Module Boundary

- 上游输入：`eval/datasets/standard_questions.jsonl` 和 `/api/analyze` 响应。
- 内部处理：`eval/scripts/run_eval.py` 在 TestClient 内调用开发者 `/api/runs` 读取最新匹配运行记录。
- 下游输出：`eval/reports/latest_eval_report.json` 中每个 case、failure、assertion_failure 增加 run trace 字段。

## Business Logic

开发者跑 `npm run eval:standard` 后，如果某个问题严格断言失败，不需要手工猜测最近 run。报告直接给出 `run_id` 和 `/api/runs/{run_id}`，可继续查看上下文召回、SQL 生成 warning、Guard 摘要和执行状态。

## Data Contract

- `EvalCaseResult.run_id`: `str | None`
- `EvalCaseResult.run_detail_path`: `str`
- 报告 JSON 的 `cases`、`failures`、`assertion_failures` 都包含上述字段。
- API 业务响应不变。

## Implementation Steps

任务清单：
- [x] 创建模块计划文档。
- [x] 实现 eval runner run trace 关联。
- [x] 增加 focused tests。
- [x] 更新评估文档和 README。
- [x] 运行 focused tests 与完整验证。
- [x] 写模块完成说明、更新 handoff、提交并推送。

## Validation Plan

- `py -3 -m pytest backend/tests/test_eval_runner.py`
- `npm run backend:test`
- `npm run eval:standard`
- `npm run frontend:build`
- `npm run test:e2e`

## Risks And Open Questions

- 评估 runner 通过开发者接口读取最近运行记录；如果未来评估并发执行，需要改为更强的请求级 correlation id。
- 当前不修改 `/api/analyze` 响应，避免把开发者 run id 暴露给普通业务界面。
