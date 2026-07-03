# 模块：SQL Memory 历史向量补齐

当前状态：本模块已完成代码、测试和文档更新，并通过全量验证，随本次提交推送完成。它不新增固定 SQL 模板，不改变普通用户前端，也不展示 embedding provider 或向量状态。

业务逻辑：新写入的 SQL Memory 已能自动保存 question/sql embedding，但旧记录可能没有向量。本模块把旧 memory 的补齐能力接入统一同步脚本，扫描缺失 `question_embedding` 或 `sql_embedding` 的记录，生成向量并回写，让历史成功 SQL 也能进入 pgvector 召回。

关键代码：

- `backend/app/services/embedding_sync_service.py`：新增 `SqlMemoryEmbeddingRecord`、`sync_sql_memory_embeddings()`、`_load_sql_memory_records()` 和 `_update_sql_memory_embeddings()`。
- `backend/scripts/sync_embeddings.py`：`--target` 新增 `memory`，默认 `all` 会依次同步 schema、metric、memory。
- `backend/tests/test_embedding_sync_service.py`：覆盖 memory 记录扫描、question/sql 双文本 embedding、双向量回写和失败不中断。

数据契约：

- 输入：`sql_memories.id`、`canonical_question`、`final_sql`。
- 输出：`sql_memories.question_embedding`、`sql_memories.sql_embedding`。
- 脚本：`py -3 backend/scripts/sync_embeddings.py --target memory`。

验证：

- `py -3 -m pytest backend/tests/test_embedding_sync_service.py`，10 passed。
- `npm run backend:test`，109 passed，1 个 `StarletteDeprecationWarning`。
- `npm run frontend:build`，通过。
- `npm run test:e2e`，通过，1 个 `StarletteDeprecationWarning`。
- `npm run eval:standard`，20/20 链路成功，严格成功率 55%。

风险/后续：

- deterministic embedding 只适合本地 fallback，真实召回质量依赖真实 embedding provider。
- 旧 memory 很多时可能需要分页和速率控制；当前 V1 先提供可运行的最小补齐闭环。
- 补齐向量不绕过 SQL Guard，fast_path 仍受关键表约束保护。
