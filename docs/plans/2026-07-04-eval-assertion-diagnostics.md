# 评估断言失败聚合诊断计划

## Goal

标准评估报告已经能列出 `assertion_failures`，但开发者还需要手工阅读每条失败，才能知道问题集中在哪些表、类别和路径。本模块在报告中增加聚合诊断字段，帮助后续优先补强通用 SQL 生成和 schema 召回，而不是继续堆固定模板。

## Current task

当前正在做：本模块已完成实现、验证、文档更新、commit 和 push。

## Scope

包含：

- 聚合链路成功但严格断言失败的案例。
- 统计缺失表次数。
- 统计失败类别次数。
- 统计失败路径次数。
- 输出需要优先关注的 case id。
- 更新测试、评估文档、handoff 和模块完成说明。

不包含：

- 不新增固定 SQL 模板。
- 不改变 `/api/analyze` 主链路。
- 不改变普通用户前端。
- 不改变标准数据集内容。

## Module boundary

上游输入：

- `EvalCaseResult` 列表。

下游输出：

- `latest_eval_report.json.assertion_failure_summary`。

预计触达文件：

- `eval/scripts/run_eval.py`
- `backend/tests/test_eval_runner.py`
- `docs/evaluation.md`
- `docs/handoff/current.md`
- `docs/modules/2026-07-04-eval-assertion-diagnostics.md`

## Business logic

开发者跑完标准评估后，应能直接看到严格失败集中在 `users`、`traffic_events`、`coupons` 等表，或集中在“用户分析”“漏斗与营销”类别，从而优先推进通用召回和模型 SQL 生成能力。

## Data contract

报告新增字段：

- `assertion_failure_summary.total`
- `assertion_failure_summary.by_missing_table`
- `assertion_failure_summary.by_category`
- `assertion_failure_summary.by_path`
- `assertion_failure_summary.case_ids`

## Implementation steps

- [x] 读取 handoff、评估报告、eval runner 和测试。
- [x] 实现聚合摘要。
- [x] 增加 focused tests。
- [x] 更新评估文档、handoff 和模块完成说明。
- [x] 运行验证。
- [x] commit 并 push。

## Validation plan

- `py -3 -m pytest backend/tests/test_eval_runner.py`
- `npm run backend:test`
- `npm run eval:standard`
- `npm run frontend:build`
- `npm run test:e2e`

## Risks and open questions

- 本模块只增强诊断，不直接提升严格成功率。
- 后续可进一步把失败 case 关联到 `query_runs` 和 `tool_calls`。
