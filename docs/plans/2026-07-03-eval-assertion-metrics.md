# 标准问题评估断言增强计划

当前正在做：标准问题评估断言增强已完成实现、测试、真实评估运行和文档更新，等待提交并推送。

## Goal

上一版评估能证明 20 个问题链路可运行，但不能充分反映 SQL 是否命中期望表、期望关键词或指标形态。本模块增加更严格的断言指标，让报告能区分“执行成功”和“更接近语义正确”。

## Scope

- 包含：
  - 增加表命中、关键词命中、严格成功等评估字段。
  - 报告新增 `table_match_rate`、`keyword_match_rate`、`strict_success_rate` 和 `assertion_failures`。
  - 更新测试和文档。
  - 重新运行标准问题评估。
- 不包含：
  - 让断言失败导致命令退出失败。
  - 完整结果数值正确性评估。
  - 前端展示评估报告。

## Module Boundary

- 上游输入：标准问题数据集和 `/api/analyze` 响应。
- 核心处理：对 SQL 文本做期望表和关键词断言。
- 下游输出：增强版 JSON 评估报告。

## Business Logic

- `ok` 继续代表 API 链路执行成功、生成 SQL、通过 Guard。
- `strict_ok` 代表链路成功且满足表命中和关键词命中。
- 评估命令保持可运行，即使断言失败也输出报告，由开发者据此定位能力缺口。

## Data Contract

- `EvalCaseResult` 新增：
  - `table_match`
  - `keyword_match`
  - `strict_ok`
  - `missing_tables`
  - `missing_keywords`
- Report 新增：
  - `strict_success_count`
  - `strict_success_rate`
  - `table_match_rate`
  - `keyword_match_rate`
  - `assertion_failures`

## Implementation Steps

任务清单：
- [x] 创建计划文档。
- [x] 实现断言指标和测试更新。
- [x] 更新 README、模块完成说明和 handoff。
- [x] 运行评估与全链路验证。
- [~] 提交并推送。

## Validation Plan

- `npm run backend:test`
- `npm run eval:standard`
- `npm run test:e2e`
- `npm run frontend:build`

## Risks and Open Questions

- 表/关键词断言仍是启发式，不等于业务语义全正确。
- 由于 SQL Memory 可能复用历史 SQL，断言失败可以暴露“问题语义被相似历史 SQL 覆盖”的风险。
