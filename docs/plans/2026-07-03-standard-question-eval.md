# 标准问题评估集基础设施计划

当前正在做：标准问题评估集基础设施已完成实现、测试、真实评估运行和文档更新，等待提交并推送。

## Goal

让每次核心改动后都能运行标准问题评估，输出执行成功率、SQL 生成成功率、记忆命中率、路径占比、平均延迟和失败案例，为后续开启模型 SQL Generator 提供可量化反馈。

## Scope

- 包含：
  - 新增 20 个标准问题 JSONL 数据集。
  - 新增自动评估脚本。
  - 生成 JSON 评估报告。
  - 增加聚焦单元测试。
  - 增加 npm 脚本。
  - 更新 README、模块完成说明和 handoff。
- 不包含：
  - 前端展示评估报告。
  - 生产级评估 dashboard。
  - 真实模型质量调优。

## Module Boundary

- 上游输入：`eval/datasets/standard_questions.jsonl`
- 核心处理：逐条调用 `/api/analyze` 或可注入分析函数，收集路径、SQL、执行状态和耗时。
- 下游输出：`eval/reports/latest_eval_report.json`

## Business Logic

- 开发者执行 `npm run eval:standard`。
- 脚本逐条运行标准问题，统计通过情况和失败案例。
- 普通用户界面不展示评估报告；报告用于开发者判断 V1 主链路健康度。

## Data Contract

- Dataset JSONL：
  - `id`
  - `category`
  - `question`
  - `expected_tables`
  - `expected_keywords`
- Report JSON：
  - `total`
  - `success_count`
  - `execution_success_rate`
  - `sql_generation_success_rate`
  - `memory_hit_rate`
  - `reuse_success_rate`
  - `average_latency_ms`
  - `path_counts`
  - `failures`
  - `cases`

## Implementation Steps

任务清单：
- [x] 创建计划文档。
- [x] 新增数据集、评估脚本和测试。
- [x] 更新 README、模块完成说明和 handoff。
- [x] 运行评估和全链路验证。
- [~] 提交并推送。

## Validation Plan

- `npm run backend:test`
- `npm run eval:standard`
- `npm run test:e2e`
- `npm run frontend:build`

## Risks and Open Questions

- 当前很多标准问题仍会走确定性回退模板，评估重点先覆盖“链路是否可运行”，不是语义满分。
- 测试仍使用本地 PostgreSQL，后续需要独立测试库或快照数据。
