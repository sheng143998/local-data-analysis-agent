# 后端可观测性与标准回归用例 V1

## 背景

本模块面向后端开发人员，目标是让一次 `/api/analyze` 请求更容易复现、定位和回归验证。重点覆盖最近出现的意图归一化、SQL 生成、聚合口径、Guard 拦截和链路耗时问题。

## 改动内容

- 标准回归用例集：
  - 新增 `eval/datasets/regression_questions.jsonl`。
  - 回归 case 支持 `expected_tables`、`expected_keywords` 和 `forbidden_keywords`。
  - `eval/scripts/run_eval.py` 新增 `load_regression_cases()`。
  - eval 结果新增 `forbidden_keyword_hits`、`forbidden_match` 和 `forbidden_match_rate`。
  - 断言失败聚合新增 `by_forbidden_keyword`，用于聚合危险 SQL 写法。
- `/api/runs/{run_id}` 调试详情：
  - `QueryRunDetail` 新增 `debug_summary`。
  - `RunService` 从已有 `tool_calls` 组装开发者摘要，包括 run、memory、context、SQL generation、intent validation、Guard、Execution、timings。
  - `query_runs.user_question` 保留用户原始问题，`rewritten_question` 保存归一化问题。
- 结构化日志：
  - `QueryRunLogger` 在创建 run 和 tool_call 后输出 `backend.observability` JSON 日志。
  - 日志仅记录摘要字段：`event`、`run_id`、`tool_name`、`status`、`latency_ms`、`output_keys`、`has_error` 等，不记录完整 prompt 或 API key。
- 链路耗时统计：
  - `analysis_graph` 在 state 中维护 `node_timings`。
  - 覆盖 `intent_parse`、`context_retrieval`、`memory_retrieval_and_plan`、`memory_sql_verification`、`sql_generation`、`sql_intent_validation`、`sql_repair`、`sql_guard`、`sql_execution`、`memory_update`、`present_result`。
  - 新增 tool call：`analysis_graph.pipeline_timings`，输出 `node_timings_ms`、`total_latency_ms` 和 `slowest_node`。
  - 主要 tool_call 的 `latency_ms` 会写入对应节点耗时。

## 验证

已通过：

```powershell
.venv\Scripts\python -m pytest backend\tests\test_runs.py backend\tests\test_eval_runner.py backend\tests\test_analysis_graph_sql_selection.py backend\tests\test_run_logger.py
```

结果：`42 passed, 1 warning`。

全量后端测试：

```powershell
npm run backend:test
```

结果：`170 passed, 3 failed, 1 warning`。失败项为 `backend/tests/test_api.py` 中仍期待旧测试 fixture SQL 成功执行的断言；当前本地未跟踪 `backend/tests/conftest.py` 的 fixture 生成了 `JOIN payments` 后直接 `SUM(o.total_amount)` 的 SQL，已被上一模块新增的重复聚合校验正确拦截。

## 注意

- 本模块不修改普通用户 UI。
- 本模块不提交真实 `.env` 密钥。
- 结构化日志默认是摘要级，后续如果需要完整 prompt，应增加显式 debug 开关和脱敏策略。
