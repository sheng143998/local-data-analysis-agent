# 模块：评估 Run Trace 摘要诊断

当前状态：本模块已完成代码开发、文档更新、完整验证、commit 和 push。提交信息为 `新增评估RunTrace摘要诊断并通过验证`，已推送到 GitHub。该模块只增强开发者评估报告，不改变普通用户前端，不新增固定 SQL 模板，不记录完整 prompt 或完整结果集。

业务逻辑：开发者运行 `npm run eval:standard` 后，每个 case 不仅有 `run_id` 和 `run_detail_path`，还会带 `run_trace_summary`。断言失败时，报告可以直接显示本次召回了哪些表、字段样例、SQL 生成路径、Guard warning/error 和 SQL Memory 规划，从而判断问题更偏向召回不足还是 SQL 生成不足。

关键代码：

- `eval/scripts/run_eval.py`
  - `EvalCaseResult` 新增 `run_trace_summary`。
  - `analyze_with_test_client()` 在找到 `run_id` 后读取 `/api/runs/{run_id}`，并写入 `_eval_run_trace_summary`。
  - `_build_run_trace_summary()` 从工具调用中提取 context、generation、guard 和 memory plan 摘要。
  - `_assertion_failure_summary()` 新增 `by_missing_table_context_status`，聚合缺失表是 `missing_from_context` 还是 `present_in_context`。
- `backend/tests/test_eval_runner.py`
  - 覆盖 run trace summary 构造、run detail 读取、报告落字段和上下文状态聚合。

数据契约：

- `eval/reports/latest_eval_report.json` 的 `cases[]`、`failures[]` 和 `assertion_failures[]` 增加：
  - `run_trace_summary.context_tables`
  - `run_trace_summary.context_fields_sample`
  - `run_trace_summary.relationship_count`
  - `run_trace_summary.generation_path`
  - `run_trace_summary.generation_warnings`
  - `run_trace_summary.guard_status`
  - `run_trace_summary.guard_errors`
  - `run_trace_summary.memory_path_type`
- `assertion_failure_summary` 增加 `by_missing_table_context_status`。

验证：

- `py -3 -m pytest backend/tests/test_eval_runner.py`，8 passed，1 个 `StarletteDeprecationWarning`。
- `npm run backend:test`，151 passed，1 个 `StarletteDeprecationWarning`。
- `npm run eval:standard`，20/20 链路成功，严格成功率 55%。
- 抽查 `eval/reports/latest_eval_report.json`：20 个 case 均包含 `run_trace_summary`；断言失败聚合显示 `users` 有 3 次未召回、1 次已召回但 SQL 未使用，`traffic_events` 3 次未召回，`coupon_usages` 2 次未召回，`coupons` 1 次未召回。
- `npm run frontend:build` 已通过。
- `npm run test:e2e` 已通过，1 个 `StarletteDeprecationWarning`。

风险/后续：

- 摘要依赖工具调用名称稳定；后续重命名工具时需要同步 eval runner。
- 当前报告已证明部分失败是召回不足，下一步应优先增强 `users`、`traffic_events`、`coupons`、`coupon_usages` 的 schema/metric 召回和模型生成策略。
