# Embedding 同步限量参数计划

## Goal

当前 embedding 同步会一次扫描目标表的全部记录。真实换库、导入新表或历史 SQL Memory 较多时，开发者需要能先小批量刷新和验证，避免一次同步耗时过长或外部 embedding provider 压力过大。本模块为 embedding 同步服务和 CLI 增加 `limit` 控制。

## Current task

当前正在做：Embedding 同步限量参数已完成实现、文档和验证，等待 commit 并 push。

## Scope

包含：

- `EmbeddingSyncService.sync_schema_embeddings()` 支持 `limit`。
- `EmbeddingSyncService.sync_metric_embeddings()` 支持 `limit`。
- `EmbeddingSyncService.sync_sql_memory_embeddings()` 支持 `limit`。
- `EmbeddingSyncService.sync_all()` 支持统一 `limit`。
- `sync_embeddings.py` 增加 `--limit` 参数。
- `refresh_context.py` 增加 `--embedding-limit` 参数并透传到 `ContextRefreshService`。
- 增加 focused tests 和文档。

不包含：

- 不新增固定 SQL 模板。
- 不改变 `/api/analyze` 主链路。
- 不改变普通用户前端。
- 不实现并发或真正批量 embedding 请求。

## Module boundary

上游输入：

- CLI 参数 `--limit` / `--embedding-limit`。
- 当前 PostgreSQL `schema_metadata`、`metric_definitions`、`sql_memories`。

下游输出：

- 本次最多同步指定数量的目标记录。
- `EmbeddingSyncResult.scanned` 表示本次实际扫描到的记录数。

预计触达文件：

- `backend/app/services/embedding_sync_service.py`
- `backend/app/services/context_refresh_service.py`
- `backend/scripts/sync_embeddings.py`
- `backend/scripts/refresh_context.py`
- `backend/tests/test_embedding_sync_service.py`
- `backend/tests/test_context_refresh_service.py`
- `README.md`
- `docs/handoff/current.md`
- `docs/modules/2026-07-04-embedding-sync-limit.md`

## Business logic

开发者可以先运行小规模同步，例如只同步 20 条 embedding，确认 provider、pgvector 和字段更新都正常后，再扩大同步范围。这样更适合真实项目从小样本到全量的推进节奏。

## Data contract

不新增 API 字段。内部服务新增可选参数：

- `limit: int | None`

CLI 新增：

- `py -3 backend/scripts/sync_embeddings.py --limit 20`
- `py -3 backend/scripts/refresh_context.py --embedding-limit 20`

## Implementation steps

- [x] 读取 handoff 和现有同步服务/脚本/测试。
- [x] 实现服务和 CLI 限量参数。
- [x] 增加 focused tests。
- [x] 更新 README、handoff 和模块完成说明。
- [x] 运行验证。
- [~] commit 并 push。

## Validation plan

- `py -3 -m pytest backend/tests/test_embedding_sync_service.py backend/tests/test_context_refresh_service.py`，19 passed
- `py -3 backend/scripts/sync_embeddings.py --help`，通过
- `py -3 backend/scripts/refresh_context.py --help`，通过
- `npm run backend:test`，120 passed，1 个 `StarletteDeprecationWarning`
- `npm run frontend:build`，通过
- `npm run test:e2e`，通过，1 个 `StarletteDeprecationWarning`
- `npm run eval:standard`，20/20 链路成功，严格成功率 55%

## Risks and open questions

- `limit` 是本次读取上限，不是全量分页调度；后续可继续增加 cursor/offset 或后台任务。
- 同一 `limit` 会应用到每个 target；如果同时同步 schema、metric、memory，三类目标分别最多同步该数量。
