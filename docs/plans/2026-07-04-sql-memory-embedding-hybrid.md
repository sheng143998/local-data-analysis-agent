# SQL Memory Embedding 混合检索计划

## Goal

让 SQL Memory 从“文本相似度临时代替语义相似度”推进到真正使用 `question_embedding` / `sql_embedding`。成功查询写入或更新 SQL Memory 时同步 embedding；检索 SQL Memory 时优先使用 pgvector 语义候选分填充 `semantic_similarity`，再与文本相似、表/指标匹配和成功率组成现有混合评分。

## Current task

当前正在做：实现 SQL Memory embedding 写入和检索端 semantic similarity 接入。

## Scope

包含：

- `SqlMemoryUpsert` 增加可选 `question_embedding` 和 `sql_embedding`。
- `SqlMemoryRepository` 在 create/update 时写入 embedding 字段。
- `upsert_successful_sql_memory()` 调用 `EmbeddingAdapter` 为问题和 SQL 生成向量。
- SQL Memory 检索调用 pgvector 候选查询，填充真实 `semantic_similarity`。
- embedding 或 pgvector 不可用时退回文本相似，不影响 `/api/analyze`。
- 增加 focused tests。
- 更新 README、SQL Memory 文档、handoff 和模块完成说明。

不包含：

- 不新增固定 SQL 模板。
- 不改变普通用户前端页面。
- 不在普通用户界面展示 SQL Memory 候选分、向量分或 provider。
- 不改变 `fast_path` / `rewrite_path` / `cold_path` 阈值。

## Module boundary

上游输入：

- 用户问题、最终 SQL、SQL Memory 的表/指标/成功率等结构化字段。
- `EmbeddingAdapter`。
- `sql_memories.question_embedding` 和 `sql_memories.sql_embedding`。

下游输出：

- `SqlMemoryCandidate.semantic_similarity` 使用 pgvector 语义分；无向量时使用文本相似回退。
- `sql_memories` 新增或更新记录时写入 question/sql embedding。

预计触达文件：

- `backend/app/schemas/memories.py`
- `backend/app/db/repositories/memory_repository.py`
- `backend/app/tools/vector_retrieval.py`
- `backend/app/tools/sql_memory_tools.py`
- `backend/tests/test_sql_memory_tools.py`
- `backend/tests/test_vector_retrieval.py`
- `README.md`
- `docs/sql_memory.md`
- `docs/handoff/current.md`
- `docs/modules/2026-07-04-sql-memory-embedding-hybrid.md`

## Business logic

业务用户反复追问相似问题时，系统应能复用历史成功 SQL，但不能只靠字面相似。SQL Memory 需要同时考虑问题语义、文本相似、涉及表和指标、历史成功率，并继续保留关键表约束，避免错误 fast_path。

## Data contract

- `SqlMemoryUpsert.question_embedding`: 可选 `list[float]`，写入 `sql_memories.question_embedding`。
- `SqlMemoryUpsert.sql_embedding`: 可选 `list[float]`，写入 `sql_memories.sql_embedding`。
- `SqlMemoryCandidate.semantic_similarity`: pgvector 语义分，失败时等于文本相似回退值。

## Implementation steps

- [x] 读取 handoff、SQL Memory 工具、仓储、schema 和测试。
- [x] 实现 memory embedding 写入。
- [x] 实现 memory pgvector 候选召回。
- [x] 接入 scoring 并增加测试。
- [x] 更新文档和模块完成说明。
- [x] 运行验证。
- [x] commit 并 push。

## Validation plan

- `npm run backend:test`，106 passed，1 个 `StarletteDeprecationWarning`
- `npm run frontend:build`，通过
- `npm run test:e2e`，通过，1 个 `StarletteDeprecationWarning`
- `npm run eval:standard`，20/20 链路成功，严格成功率 55%

## Risks and open questions

- deterministic embedding 只是本地 fallback，真实语义质量需要真实 embedding provider。
- 已有历史 memory 若没有 embedding，会自动退回文本相似；可通过后续脚本批量补齐旧记录。
- fast_path 安全仍依赖关键表约束和 SQL Guard，不能因为向量高分绕过安全链路。
