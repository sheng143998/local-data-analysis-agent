# 模块：运行日志上下文诊断增强

当前状态：本模块已完成运行日志 payload 增强、完整验证、commit 和 push。提交信息为 `增强运行日志上下文诊断并通过验证`，已推送到 GitHub。它不改变普通用户前端，不新增固定 SQL 模板，不记录完整 prompt 或完整结果集。

业务逻辑：开发者通过 `/api/runs/{run_id}` 查看一次分析运行时，可以直接看到上下文召回规模、表关系数量、SQL 生成 warning 和 Guard warning/error 摘要。这样标准评估或真实问答失败后，不需要马上翻后端日志，就能判断是 schema 召回不足、SQL 生成异常，还是 Guard 拦截导致。

关键代码：

- `backend/app/agents/analysis_graph.py`
  - `_log_analysis_run()` 新增 `relationship_count`、`context_tables`、`context_fields`、`generation_warnings`、`guard_warnings`、`guard_errors`。
  - `context_builder.build_retrieval_context` 的 `output_payload` 增加召回表、字段样例和表关系数。
  - `analysis_graph.select_generated_sql` 的 `output_payload` 增加 `has_sql`、`warning_count` 和 warning 样例。
  - `sql_validation_tools.guard_sql` 的 `output_payload` 增加 warning/error 数量和样例。
- `backend/tests/test_runs.py`
  - 覆盖 `/api/runs/{run_id}` 返回增强后的工具调用摘要。

数据契约：

- 数据库结构不变。
- `tool_calls.output_payload` 增加 JSON 摘要字段：
  - `relationship_count`
  - `tables`
  - `fields_sample`
  - `has_sql`
  - `warning_count`
  - `warnings`
  - `error_count`
  - `errors`

验证：

- `py -3 -m pytest backend/tests/test_runs.py`，3 passed，1 个 `StarletteDeprecationWarning`。
- `npm run backend:test`，142 passed，1 个 `StarletteDeprecationWarning`。
- `npm run eval:standard`，20/20 链路成功，严格成功率 55%。
- `npm run frontend:build` 已通过。
- `npm run test:e2e` 已通过，1 个 `StarletteDeprecationWarning`。

风险/后续：

- 当前只记录样例和摘要，不记录完整 prompt 或完整结果集，避免调试表膨胀和敏感信息扩散。
- `/api/runs` 仍是开发者调试接口，上线或多人使用前需要权限控制。
