模块：SQL 关键上下文表覆盖检查

当前状态：已完成代码、文档和全链路验证，待本次提交并推送。

业务逻辑：当用户问题召回了用户、流量、优惠券等非默认业务表，但 SQL Memory rewrite 或确定性 SQL 生成仍只查询订单、支付等基础交易表时，系统会识别为“上下文表覆盖不足”。模型 SQL Generator 关闭时，后端保留当前稳定 SQL 结果并写入内部 warning；模型开关开启时，会把该请求转为模型 cold path，要求模型基于已召回 schema 重新生成覆盖关键表的 SQL。该能力不新增固定 SQL 模板，也不在普通用户界面展示调试细节。

关键代码：
- `backend/app/agents/analysis_graph.py`：新增 `_context_table_coverage()`、`_required_context_tables()`、`_extract_sql_tables()` 和 `_context_table_coverage_warning()`；`_select_generated_sql()` 在确定性 SQL 后检查关键上下文表覆盖，必要时尝试模型 cold path。
- `backend/app/agents/analysis_graph.py`：`analysis_graph.select_generated_sql` 的工具调用输出新增 `context_table_coverage`，开发者可从 `/api/runs/{run_id}` 查看 `required_tables`、`sql_tables`、`missing_tables` 和 `covered`。
- `backend/tests/test_analysis_graph_sql_selection.py`：新增模型关闭 warning、模型开启转向、覆盖诊断结构三类测试。

数据契约：不改变普通 `/api/analyze` 用户响应契约。内部 `tool_calls.output_payload.context_table_coverage` 新增字段：
- `required_tables`：当前上下文中需要强覆盖的非默认业务表。
- `sql_tables`：从最终 SQL 解析出的真实表名。
- `missing_tables`：已召回但 SQL 未使用的关键表。
- `covered`：是否全部覆盖。

验证：
- `py -3 -m pytest backend/tests/test_analysis_graph_sql_selection.py`，7 passed
- `npm run backend:test`，158 passed，1 个 `StarletteDeprecationWarning`
- `npm run eval:standard`，20/20 链路成功，`strict_success_rate=55.00%`
- `npm run frontend:build`，通过
- `npm run test:e2e`，通过，1 个 `StarletteDeprecationWarning`

风险/后续：默认模型 SQL Generator 关闭时，本模块主要提供诊断和防错 warning，不能直接提升所有复杂问题的严格成功率。下一步可在真实本地模型可用后开启 `MODEL_SQL_GENERATOR_ENABLED=true` 跑标准评估，重点观察 `context_table_coverage.missing_tables` 是否下降。
