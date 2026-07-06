# 后端可观测性与标准回归用例 V1 计划

## Goal

面向后端开发人员增强问题复现、链路定位和日志排障能力。重点覆盖最近暴露的意图解析、SQL 生成、聚合口径和 run trace 可观测性问题。

## Scope

包含：
- 新增标准回归用例集，沉淀“总销售额 vs 平均销售额”“payments join 重复聚合”等高价值问题。
- 增强 `/api/runs/{run_id}` 调试详情，输出意图解析、SQL 生成、SQL 意图校验、Guard/Executor、repair 和链路耗时摘要。
- 后端结构化日志新增 JSON 或半结构化事件，开发时可从日志直接看到 run_id、节点、耗时、决策和 warning 数量。
- 增加链路耗时统计，覆盖 intent、context retrieval、memory、SQL generation、validation、guard、execution、present、log_run 等主要节点。
- 增加 focused tests，避免依赖真实模型或真实 API key。
- 更新模块文档和 handoff，提交并推送。

不包含：
- 不修改普通用户 UI。
- 不提交真实 `.env` 密钥。
- 不引入外部日志平台。
- 不重构现有数据库表结构，优先复用 `query_runs` 和 `tool_calls`。

## Implementation steps

- [x] 创建本计划文档。
- [x] 阅读 runs、eval、analysis graph、logger 相关代码。
- [x] 新增标准回归用例集和测试入口。
- [x] 增强 run detail 的开发者调试摘要。
- [x] 增加结构化日志工具并接入分析链路。
- [x] 增加节点耗时统计并写入 run trace。
- [x] 更新 focused tests。
- [x] 运行 focused tests。
- [x] 补模块完成文档并更新 handoff。

## Validation plan

- `.venv\Scripts\python -m pytest backend\tests\test_runs.py backend\tests\test_eval_runner.py backend\tests\test_analysis_graph_sql_selection.py`
- 如改动涉及 API contract，再补跑 `npm run backend:test`。

## Risks

- run trace payload 会变大，需要避免记录完整敏感 prompt 或 API key。
- 结构化日志默认只记录摘要，不记录完整 SQL prompt；后续如需完整 prompt，应单独加显式 debug 开关。
