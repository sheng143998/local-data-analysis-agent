# Query Run Logging 运行记录模块计划

## Goal

把 `/api/analyze` 每次数据问答运行写入 PostgreSQL 的 `query_runs`，并把关键工具调用写入 `tool_calls`，让 V1 主链路具备可追踪、可调试、可评估的运行证据。

## 当前正在做

当前正在做：Query Run Logging 最小切片已完成，已提交并推送。

## Scope

包含：

- 新增 `query_runs` / `tool_calls` Pydantic schema。
- 新增 PostgreSQL repository 和 service。
- 在 `analysis_graph.py` 中记录 schema/metric retrieval、SQL Guard、SQL Executor、Result Presenter。
- 新增 `/api/runs` 和 `/api/runs/{run_id}` 调试查询接口。
- 更新 README、模块文档、handoff 和测试。

不包含：

- 前端开发者调试页。
- SQL Memory 写入和复用。
- 评估报告页面。
- LLM / embedding 调用日志。

## Module Boundary

- 上游输入：用户问题、检索上下文、Guard 结果、Executor 结果、Presenter 输出。
- 下游输出：`query_runs`、`tool_calls` 数据库记录，以及只读调试 API。
- 可能触达文件：
  - `backend/app/schemas/runs.py`
  - `backend/app/db/repositories/run_repository.py`
  - `backend/app/services/run_service.py`
  - `backend/app/api/runs.py`
  - `backend/app/api/routes.py`
  - `backend/app/tools/run_logger.py`
  - `backend/app/agents/analysis_graph.py`
  - `backend/tests/test_runs.py`
  - `README.md`
  - `docs/modules/2026-07-03-query-run-logging.md`
  - `docs/handoff/current.md`

## Business Logic

业务用户完成一次数据问答后，系统留下可审计的运行记录：问题是什么、最终执行 SQL 是什么、Guard 是否通过、SQL 是否执行成功、返回多少行、耗时多少、失败原因是什么。开发者可以通过 `/api/runs` 查看关键工具调用摘要，但普通用户界面不默认展示这些调试细节。

## Data Contract

- `QueryRunRecord`
  - `id`
  - `user_question`
  - `rewritten_question`
  - `memory_hit`
  - `memory_id`
  - `generated_sql`
  - `final_sql`
  - `guard_status`
  - `execution_status`
  - `row_count`
  - `latency_ms`
  - `error_message`
  - `created_at`
- `ToolCallRecord`
  - `id`
  - `query_run_id`
  - `tool_name`
  - `input_payload`
  - `output_payload`
  - `status`
  - `latency_ms`
  - `error_message`
  - `created_at`
- API：
  - `GET /api/runs`
  - `GET /api/runs/{run_id}`

## Implementation Steps

任务清单：

- [x] 读取 handoff、草案和现有 analyze 链路。
- [x] 创建本计划文档。
- [x] 实现 schema、repository、service、API。
- [x] 接入 `analysis_graph.py` 落库。
- [x] 补测试和 README。
- [x] 运行验证。
- [x] 更新模块文档和 handoff。
- [x] commit 并 push。

## Validation Plan

- `npm run backend:test`：已通过，20 个测试通过。
- `npm run test:e2e`：已通过，FastAPI smoke 闭环通过。
- `npm run frontend:build`：已通过，Vite production build 成功。
- `GET /api/runs` 已由 `backend/tests/test_runs.py` 覆盖，能返回最新 analyze 运行记录。

## Risks and Open Questions

- 当前只记录结构化摘要，不记录完整大结果集，避免日志表膨胀。
- 当前 `/api/runs` 是开发者调试接口，暂不放入普通用户前端主导航。
