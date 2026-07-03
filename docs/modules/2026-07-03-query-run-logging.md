# 模块：Query Run Logging 运行记录

当前状态：模块已完成，已通过 `npm run backend:test`、`npm run test:e2e` 和 `npm run frontend:build` 验证，已提交并推送到 GitHub。

业务逻辑：每次用户通过 `/api/analyze` 发起数据问答后，系统会把本次运行写入 `query_runs`，记录用户问题、最终 SQL、Guard 状态、执行状态、返回行数、总耗时和错误信息；同时把关键工具调用写入 `tool_calls`，包括上下文召回、SQL Guard、SQL Executor 和结果整理。普通用户仍只看到分析结果，开发者可通过 `/api/runs` 查看运行证据。

关键代码：

- `backend/app/schemas/runs.py`：定义 `QueryRunRecord`、`QueryRunDetail`、`ToolCallRecord`、`QueryRunCreate` 和 `ToolCallCreate`。
- `backend/app/db/repositories/run_repository.py`：封装 `query_runs` 和 `tool_calls` 的 PostgreSQL 读写。
- `backend/app/services/run_service.py`：提供运行记录查询服务，并限制列表查询 `limit` 在 1-100。
- `backend/app/api/runs.py`：新增 `GET /api/runs` 和 `GET /api/runs/{run_id}`。
- `backend/app/tools/run_logger.py`：提供 `QueryRunLogger`，供 Agent 编排层记录 run 和 tool call。
- `backend/app/agents/analysis_graph.py`：在 analyze 链路完成后写入运行记录和四个工具调用摘要。
- `backend/tests/test_runs.py`：覆盖 analyze 后写入运行记录、工具调用明细和缺失 run 的 404。

数据契约：`query_runs` 记录一次分析运行，核心字段为 `user_question`、`generated_sql`、`final_sql`、`guard_status`、`execution_status`、`row_count`、`latency_ms`、`error_message`；`tool_calls` 记录工具名、输入摘要、输出摘要、状态、耗时和错误信息；`GET /api/runs/{run_id}` 返回 run 详情和按创建时间排序的 `tool_calls`。

验证：`npm run backend:test` 已通过，20 passed，包含 API、指标 CRUD、retriever、run logging、SQL Guard、SQL Executor；`npm run test:e2e` 已通过，确认 question -> FastAPI -> AgentService -> Guard -> Executor -> result 闭环仍可运行；`npm run frontend:build` 已通过，确认前端构建未受后端调试 API 影响。`FastAPI TestClient` 仍有 `StarletteDeprecationWarning`，不影响功能。

风险/后续：当前只记录关键摘要，不记录完整查询结果集，避免日志表膨胀；`/api/runs` 是开发者调试接口，暂未接入普通用户前端；下一步可继续做 SQL Memory Retriever / Reuse Planner。
