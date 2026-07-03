# 模块完成说明：只读 SQL Executor

模块：只读 SQL Executor

当前状态：已完成，Executor 只接受 SQL Guard 放行后的 `final_sql`，并已通过后端测试、smoke 和前端构建。

业务逻辑：
- LLM 或模板生成的 SQL 不能直接执行。
- SQL 必须先经过 Guard，只有 `allowed=True` 且存在 `final_sql` 时 Executor 才执行。
- Executor 返回结构化结果：执行状态、列名、行数据、行数、耗时和错误信息。
- 被 Guard 拦截的 SQL 返回 `blocked`，数据库执行错误返回 `error`。

关键代码：
- `backend/app/schemas/sql_execution.py`：定义 `SqlExecutionResult`。
- `backend/app/tools/sql_execution_tools.py`：实现 `execute_guarded_sql`。
- `backend/tests/test_sql_execution_tools.py`：覆盖成功执行、Guard 拦截、运行时错误。

数据契约：
- `SqlExecutionResult.status`: `success` / `error` / `blocked`
- `columns`: 结果列
- `rows`: JSON-friendly 行数据
- `row_count`: 返回行数
- `latency_ms`: 执行耗时
- `error_message`: 错误信息

验证：
- `npm run backend:test`
- `npm run test:e2e`
- `npm run frontend:build`

风险/后续：
- 当前 Executor 未写入 `query_runs`。
- 当前未设置数据库 statement timeout。
- 下一步应把 `/api/analyze` 从 mock graph 逐步接入 Guard + Executor。
