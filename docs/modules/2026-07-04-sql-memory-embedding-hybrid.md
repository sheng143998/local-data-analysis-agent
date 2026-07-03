# 模块：SQL Memory Embedding 混合检索

当前状态：本模块已完成代码、测试和文档更新，并通过全量验证，随本次提交推送完成。它不新增固定 SQL 模板，不改变普通用户前端，也不展示 SQL Memory 候选分、向量分或 provider。

业务逻辑：用户重复提出相似问题时，SQL Memory 不再只靠文本相似。成功查询写入或更新 memory 时，系统会为用户问题和最终 SQL 生成 embedding 并写入 `sql_memories.question_embedding` / `sql_memories.sql_embedding`。检索历史 memory 时，系统优先使用问题向量在 pgvector 中召回语义候选，再与文本相似、表/指标匹配和成功率组成原有混合评分。向量不可用时自动回退文本相似。

关键代码：

- `backend/app/schemas/memories.py`：`SqlMemoryUpsert` 增加 `question_embedding` 和 `sql_embedding`。
- `backend/app/db/repositories/memory_repository.py`：create/update SQL Memory 时写入两个向量字段。
- `backend/app/tools/vector_retrieval.py`：新增 `retrieve_sql_memory_vector_candidates()`，查询 `sql_memories.question_embedding`。
- `backend/app/tools/sql_memory_tools.py`：`retrieve_sql_memory()` 接入语义候选分；`upsert_successful_sql_memory()` 调用 `EmbeddingAdapter` 生成 question/sql embedding。
- `backend/tests/test_sql_memory_tools.py`、`backend/tests/test_vector_retrieval.py`：覆盖语义分排序、文本回退、向量写入 payload 和 pgvector 查询形状。

数据契约：

- `SqlMemoryUpsert.question_embedding`: 可选向量，写入 `sql_memories.question_embedding`。
- `SqlMemoryUpsert.sql_embedding`: 可选向量，写入 `sql_memories.sql_embedding`。
- `SqlMemoryCandidate.semantic_similarity`: 优先为 pgvector 分数，无候选时回退文本相似。

验证：

- `py -3 -m pytest backend/tests/test_sql_memory_tools.py backend/tests/test_vector_retrieval.py`，15 passed。
- `npm run backend:test`，106 passed，1 个 `StarletteDeprecationWarning`。
- `npm run frontend:build`，通过。
- `npm run test:e2e`，通过，1 个 `StarletteDeprecationWarning`。
- `npm run eval:standard`，20/20 链路成功，严格成功率 55%。

风险/后续：

- deterministic embedding 只适合本地 fallback，真实语义质量依赖真实 embedding provider。
- 旧 SQL Memory 没有 embedding 时会回退文本相似；后续可做批量补齐脚本。
- fast_path 仍必须满足关键表约束，并且最终 SQL 仍必经 SQL Guard 和只读 Executor。
