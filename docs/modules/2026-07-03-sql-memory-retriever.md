# 模块：SQL Memory Retriever / Reuse Planner 最小切片

当前状态：模块已完成，已通过 `npm run backend:test`、`npm run test:e2e` 和 `npm run frontend:build` 验证，已提交并推送到 GitHub。

业务逻辑：每次用户通过 `/api/analyze` 发起数据问答时，系统先基于用户问题、召回指标和相关表检索 `sql_memories`。如果存在高置信历史成功 SQL，则走 `fast_path` 直接复用该 SQL，但仍会经过 SQL Guard 和只读 Executor；如果没有高置信命中，则继续走当前固定销售趋势 SQL 模板的 `cold_path`。查询成功后，系统会写入或更新 SQL Memory，记录问题、SQL、相关表、指标、结果列、行数、延迟和成功次数。普通用户不看到候选评分，开发者可通过 `/api/memories` 和 `/api/runs` 查看复用证据。

关键代码：

- `backend/app/schemas/memories.py`：定义 `SqlMemoryRecord`、`SqlMemoryCandidate`、`SqlReusePlan` 和 `SqlMemoryUpsert`。
- `backend/app/db/repositories/memory_repository.py`：封装 `sql_memories` 的读取、按标准化问题 upsert、成功次数和平均延迟更新。
- `backend/app/tools/sql_memory_tools.py`：实现 `retrieve_sql_memory`、`plan_sql_reuse` 和 `upsert_successful_sql_memory`。
- `backend/app/tools/text_normalization.py`：统一问题标准化逻辑，供 SQL Memory 文本匹配使用。
- `backend/app/api/memories.py` 与 `backend/app/services/memory_service.py`：提供 `/api/memories` 和 `/api/memories/{memory_id}` 开发者调试接口。
- `backend/app/agents/analysis_graph.py`：接入 memory 检索、复用规划、成功写入和运行记录。
- `backend/app/tools/analysis_presenter.py`：将 `AnalyzeResponse.path`、`trace.memoryCandidates` 和步骤文案与复用计划联动。
- `backend/tests/test_sql_memory_tools.py`：覆盖高置信 memory 召回、`fast_path` 规划和无候选 `cold_path`。

数据契约：`SqlMemoryRecord` 映射 `sql_memories` 表，核心字段包括 `canonical_question`、`normalized_question`、`sql_template`、`final_sql`、`tables`、`metrics`、`success_count`、`failure_count`、`avg_latency_ms`、`last_result_columns`、`last_row_count` 和 `last_used_at`；`SqlReusePlan` 输出 `path_type`、`reuse_type`、`memory_hit`、`selected_memory_id`、`selected_sql`、`candidate_count` 和 `score`；`GET /api/memories` 返回开发者可读的历史成功 SQL 列表。

验证：`npm run backend:test` 已通过，24 passed，覆盖 API、指标 CRUD、retriever、runs、SQL Guard、SQL Executor 和 SQL Memory 工具；`npm run test:e2e` 已通过，确认 question -> FastAPI -> AgentService -> Guard -> Executor -> result 闭环仍可运行；`npm run frontend:build` 已通过，确认前端构建未受后端调试 API 影响。`FastAPI TestClient` 仍有 `StarletteDeprecationWarning`，不影响功能。

风险/后续：当前 semantic similarity 暂用文本相似度作为 deterministic fallback，尚未接入 embedding / pgvector；低置信候选暂不触发 LLM rewrite；下一步建议继续补 SQL Memory 参数化模板和 Rewriter/Generator。
