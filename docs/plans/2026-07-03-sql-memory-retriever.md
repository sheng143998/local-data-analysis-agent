# SQL Memory Retriever / Reuse Planner 最小切片计划

## Goal

让 `/api/analyze` 在执行固定 SQL 模板前先检索 `sql_memories`，对高置信历史成功 SQL 走 `fast_path`，并在查询成功后写入或更新 SQL Memory，为后续 Rewriter、Generator 和评估打基础。

## 当前正在做

当前正在做：SQL Memory 检索、复用规划、成功写入和 `/api/memories` 调试接口已完成，已提交并推送。

## Scope

包含：

- 新增 SQL Memory Pydantic schema。
- 新增 PostgreSQL `sql_memories` repository 和 service。
- 新增 `retrieve_sql_memory`、`plan_sql_reuse`、`upsert_successful_sql_memory` 工具。
- 在 `analysis_graph.py` 中接入 memory retrieval、reuse planner 和 memory updater。
- 新增 `/api/memories` 和 `/api/memories/{memory_id}` 开发者调试接口。
- 更新测试、README、模块文档和 handoff。

不包含：

- 真实 embedding / pgvector 语义召回。
- LLM SQL Rewriter / Generator。
- 前端开发者调试页。
- 复杂参数化模板渲染。

## Module Boundary

- 上游输入：用户问题、retrieval context 中的指标和表。
- 下游输出：`SqlReusePlan`、`AnalyzeResponse.path`、`query_runs.memory_hit`、`sql_memories` 写入记录、`/api/memories` 调试接口。
- 可能触达文件：
  - `backend/app/schemas/memories.py`
  - `backend/app/db/repositories/memory_repository.py`
  - `backend/app/services/memory_service.py`
  - `backend/app/api/memories.py`
  - `backend/app/tools/sql_memory_tools.py`
  - `backend/app/agents/analysis_graph.py`
  - `backend/app/tools/analysis_presenter.py`
  - `backend/app/tools/run_logger.py`
  - `backend/tests/test_sql_memory_tools.py`
  - `backend/tests/test_api.py`
  - `README.md`
  - `docs/modules/2026-07-03-sql-memory-retriever.md`
  - `docs/handoff/current.md`

## Business Logic

当用户提出与历史成功问题高度一致的问题时，系统优先复用已经验证过的 SQL，仍然经过 SQL Guard 和只读 Executor；当没有高置信命中时，继续走现有固定模板冷启动链路。查询成功后，系统把问题、SQL、相关表、指标、结果结构和成功次数写入 SQL Memory。普通用户不看到候选评分，开发者通过 `/api/memories` 和 `/api/runs` 查看复用证据。

## Data Contract

- `SqlMemoryRecord`
  - `id`
  - `canonical_question`
  - `normalized_question`
  - `sql_template`
  - `final_sql`
  - `tables`
  - `metrics`
  - `dimensions`
  - `success_count`
  - `failure_count`
  - `avg_latency_ms`
  - `last_result_columns`
  - `last_row_count`
  - `last_used_at`
  - `created_at`
- `SqlMemoryCandidate`
  - `memory`
  - `score`
  - `semantic_similarity`
  - `text_similarity`
  - `metric_table_match`
  - `success_score`
- `SqlReusePlan`
  - `path_type`
  - `reuse_type`
  - `memory_hit`
  - `selected_memory_id`
  - `selected_sql`
  - `candidate_count`
  - `score`

## Implementation Steps

任务清单：

- [x] 读取 handoff、草案和当前 analyze 链路。
- [x] 创建本计划文档。
- [x] 实现 SQL Memory schema、repository、service 和 API。
- [x] 实现 retrieval / reuse / updater 工具并接入 analyze。
- [x] 补充测试、README、模块文档和 handoff。
- [x] 运行验证。
- [x] commit 并 push。

## Validation Plan

- `npm run backend:test`：已通过，24 个测试通过。
- `npm run test:e2e`：已通过，FastAPI smoke 闭环通过。
- `npm run frontend:build`：已通过，Vite production build 成功。

## Risks and Open Questions

- 当前语义相似度使用文本相似度作为 deterministic fallback，后续需要接 embedding / pgvector。
- 当前只对高置信 memory 走 `fast_path`，低置信候选暂不触发 LLM rewrite。
