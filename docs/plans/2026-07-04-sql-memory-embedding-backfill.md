# SQL Memory 历史向量补齐计划

## Goal

为已有 SQL Memory 补齐 `question_embedding` 和 `sql_embedding`，避免旧记录长期只能走文本相似回退，让 SQL Memory 混合检索对历史成功 SQL 也生效。本模块不新增固定 SQL 模板，不改变普通用户前端，不展示向量状态。

## Current task

当前正在做：扩展 embedding 同步服务和脚本，支持 `--target memory`。

## Scope

包含：

- `EmbeddingSyncService` 增加 SQL Memory 历史记录同步。
- `backend/scripts/sync_embeddings.py` 支持 `--target memory`，默认 `all` 包含 schema、metric、memory。
- 只扫描 `question_embedding IS NULL OR sql_embedding IS NULL` 的历史 memory。
- 调用 `EmbeddingAdapter` 为 canonical question 和 final SQL 生成向量。
- 回写 `sql_memories.question_embedding` 和 `sql_memories.sql_embedding`。
- 增加 focused tests。
- 更新 README、SQL Memory 文档、handoff 和模块完成说明。

不包含：

- 不改变 `/api/analyze` SQL 生成逻辑。
- 不新增固定模板。
- 不改变普通用户页面。
- 不新增数据库 migration，字段已在 `003_agent_metadata.sql` 中存在。

## Module boundary

上游输入：

- `sql_memories.id`
- `sql_memories.canonical_question`
- `sql_memories.final_sql`
- `EmbeddingAdapter`

下游输出：

- `sql_memories.question_embedding`
- `sql_memories.sql_embedding`
- `EmbeddingSyncResult(target="memory")`

预计触达文件：

- `backend/app/services/embedding_sync_service.py`
- `backend/scripts/sync_embeddings.py`
- `backend/tests/test_embedding_sync_service.py`
- `README.md`
- `docs/sql_memory.md`
- `docs/handoff/current.md`
- `docs/modules/2026-07-04-sql-memory-embedding-backfill.md`

## Business logic

新写入的 SQL Memory 已能自动保存 embedding，但项目中已有的历史 memory 仍可能没有向量。补齐脚本让历史成功问题也进入 pgvector 召回，减少“新能力只对新数据生效”的断层。

## Data contract

脚本：

```bash
py -3 backend/scripts/sync_embeddings.py --target memory
py -3 backend/scripts/sync_embeddings.py --target all
```

`EmbeddingSyncResult`：

- `target`: `memory`
- `scanned`: 缺失 question/sql embedding 的 memory 数
- `updated`: 成功写入向量数
- `failed`: 失败数
- `errors`: 错误摘要

## Implementation steps

- [x] 读取 handoff、embedding sync、SQL Memory 写入和测试。
- [x] 扩展同步服务和脚本。
- [x] 增加单元测试。
- [x] 更新文档和模块完成说明。
- [x] 运行验证。
- [x] commit 并 push。

## Validation plan

- `npm run backend:test`，109 passed，1 个 `StarletteDeprecationWarning`
- `npm run frontend:build`，通过
- `npm run test:e2e`，通过，1 个 `StarletteDeprecationWarning`
- `npm run eval:standard`，20/20 链路成功，严格成功率 55%

## Risks and open questions

- deterministic embedding 只适合本地 fallback，真实语义质量依赖真实 embedding provider。
- 历史 SQL 很多时后续可增加批量大小和进度分页；V1 先实现可运行的最小闭环。
- 真实生产环境补齐前应确认 embedding provider 成本和速率限制。
