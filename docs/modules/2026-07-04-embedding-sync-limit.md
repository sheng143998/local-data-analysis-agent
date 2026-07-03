# 模块：Embedding 同步限量参数

当前状态：本模块已完成服务、CLI、focused tests、完整验证和文档更新，等待 commit 和 push。它不新增固定 SQL 模板，不改变普通用户前端，不改变 `/api/analyze` 主链路。

业务逻辑：真实换库或历史 SQL Memory 较多时，开发者可以先用小批量同步验证 embedding provider、pgvector 写入和检索资产刷新，再扩大同步范围，降低一次全量同步的耗时和失败成本。

关键代码：

- `backend/app/services/embedding_sync_service.py`：`sync_schema_embeddings()`、`sync_metric_embeddings()`、`sync_sql_memory_embeddings()` 和 `sync_all()` 新增 `limit` 参数，并在查询层追加 `LIMIT %s`。
- `backend/app/services/context_refresh_service.py`：`refresh()` 新增 `embedding_limit`，一键刷新时透传给 embedding 同步。
- `backend/scripts/sync_embeddings.py`：新增 `--limit`。
- `backend/scripts/refresh_context.py`：新增 `--embedding-limit`。
- `backend/tests/test_embedding_sync_service.py` 和 `backend/tests/test_context_refresh_service.py`：覆盖 limit 参数、SQL 参数化和透传行为。

数据契约：

- 不新增 API 字段。
- 内部服务新增可选参数 `limit: int | None`。
- CLI 新增 `--limit` / `--embedding-limit`，同一限制会分别应用到每个同步 target。

验证：

- `py -3 -m pytest backend/tests/test_embedding_sync_service.py backend/tests/test_context_refresh_service.py`，19 passed。
- `py -3 backend/scripts/sync_embeddings.py --help`，通过。
- `py -3 backend/scripts/refresh_context.py --help`，通过。
- `npm run backend:test`，120 passed，1 个 `StarletteDeprecationWarning`。
- `npm run frontend:build`，通过。
- `npm run test:e2e`，通过，1 个 `StarletteDeprecationWarning`。
- `npm run eval:standard`，20/20 链路成功，严格成功率 55%。

风险/后续：

- `limit` 是本次同步上限，不是分页游标；后续可继续做 offset/cursor 或后台任务。
- 当前仍逐条调用 embedding adapter，未实现批量 embedding 请求或并发。
