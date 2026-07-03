# Embedding 同步批量请求计划

## Goal

当前 embedding 同步虽然支持 `limit`，但仍逐条调用 `EmbeddingAdapter`。真实 embedding provider 下，这会造成大量网络请求。本模块增加 `batch_size`，让 schema、metric 和 SQL Memory 同步可以把多条文本放入一次 embedding 请求，降低请求次数。

## Current task

当前正在做：Embedding 同步批量请求已完成实现、文档和验证，等待 commit 并 push。

## Scope

包含：

- `EmbeddingSyncService.sync_schema_embeddings()` 支持 `batch_size`。
- `EmbeddingSyncService.sync_metric_embeddings()` 支持 `batch_size`。
- `EmbeddingSyncService.sync_sql_memory_embeddings()` 支持 `batch_size`。
- `EmbeddingSyncService.sync_all()` 支持统一 `batch_size`。
- `ContextRefreshService.refresh()` 支持 `embedding_batch_size`。
- `sync_embeddings.py` 增加 `--batch-size`。
- `refresh_context.py` 增加 `--embedding-batch-size`。
- 增加 focused tests 和文档。

不包含：

- 不新增固定 SQL 模板。
- 不改变普通用户前端。
- 不改变 `/api/analyze` 主链路。
- 不实现并发、限速或后台队列。

## Module boundary

上游输入：

- CLI 参数 `--batch-size` / `--embedding-batch-size`。
- 当前 `schema_metadata`、`metric_definitions`、`sql_memories` 记录。

下游输出：

- 与原来相同的 embedding 写回字段。
- `EmbeddingSyncResult.scanned/updated/failed/errors` 语义保持不变。

预计触达文件：

- `backend/app/services/embedding_sync_service.py`
- `backend/app/services/context_refresh_service.py`
- `backend/scripts/sync_embeddings.py`
- `backend/scripts/refresh_context.py`
- `backend/tests/test_embedding_sync_service.py`
- `backend/tests/test_context_refresh_service.py`
- `README.md`
- `docs/data_model.md`
- `docs/handoff/current.md`
- `docs/modules/2026-07-04-embedding-sync-batch.md`

## Business logic

开发者同步向量资产时，可以用较小的 batch_size 控制 provider 压力，也可以调大 batch_size 降低请求次数。SQL Memory 每条记录需要两个向量：问题向量和 SQL 向量；批量请求会保持成对顺序写回。

## Data contract

不新增 API 字段。内部服务新增可选参数：

- `batch_size: int = 16`

CLI 新增：

- `py -3 backend/scripts/sync_embeddings.py --batch-size 16`
- `py -3 backend/scripts/refresh_context.py --embedding-batch-size 16`

## Implementation steps

- [x] 读取 handoff、EmbeddingAdapter 和同步服务。
- [x] 实现服务和 CLI 批量参数。
- [x] 增加 focused tests。
- [x] 更新 README、handoff 和模块完成说明。
- [x] 运行验证。
- [~] commit 并 push。

## Validation plan

- `py -3 -m pytest backend/tests/test_embedding_sync_service.py backend/tests/test_context_refresh_service.py`，25 passed
- `py -3 backend/scripts/sync_embeddings.py --help`，通过
- `py -3 backend/scripts/refresh_context.py --help`，通过
- `npm run backend:test`，126 passed，1 个 `StarletteDeprecationWarning`
- `npm run frontend:build`，通过
- `npm run test:e2e`，通过，1 个 `StarletteDeprecationWarning`
- `npm run eval:standard`，20/20 链路成功，严格成功率 55%

## Risks and open questions

- 当前批量失败会让该 batch 内记录全部失败；后续可加 batch 失败后的单条重试。
- 本模块不做并发和限速，真实 provider 的速率控制后续另做。
