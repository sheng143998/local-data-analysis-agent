# 模块：Embedding 同步批量请求

当前状态：本模块已完成服务、CLI、focused tests、完整验证和文档更新，等待 commit 和 push。它不新增固定 SQL 模板，不改变普通用户前端，不改变 `/api/analyze` 主链路。

业务逻辑：真实 embedding provider 下，逐条同步 schema、metric 和 SQL Memory 会产生大量网络请求。本模块让同步服务按 `batch_size` 把多条文本合并成一次 embedding 请求，降低请求次数。SQL Memory 会保持“问题文本 + SQL 文本”的顺序成对写回。

关键代码：

- `backend/app/services/embedding_sync_service.py`：schema、metric、memory 和 all 同步入口新增 `batch_size`；schema/metric 按文档批量请求，memory 按问题/SQL 成对批量请求。
- `backend/app/services/context_refresh_service.py`：新增 `embedding_batch_size` 并透传到 embedding 同步。
- `backend/scripts/sync_embeddings.py`：新增 `--batch-size`。
- `backend/scripts/refresh_context.py`：新增 `--embedding-batch-size`。
- `backend/tests/test_embedding_sync_service.py`：覆盖 schema/metric 批量写回、memory 成对向量写回、短响应整批失败和非法 batch size。
- `backend/tests/test_context_refresh_service.py`：覆盖刷新服务透传 batch size。

数据契约：

- 不新增 API 字段。
- 内部服务新增可选参数 `batch_size: int = 16`。
- CLI 新增 `--batch-size` / `--embedding-batch-size`。
- `EmbeddingSyncResult.scanned/updated/failed/errors` 语义保持不变。

验证：

- `py -3 -m pytest backend/tests/test_embedding_sync_service.py backend/tests/test_context_refresh_service.py`，25 passed。
- `py -3 backend/scripts/sync_embeddings.py --help`，通过。
- `py -3 backend/scripts/refresh_context.py --help`，通过。
- `npm run backend:test`，126 passed，1 个 `StarletteDeprecationWarning`。
- `npm run frontend:build`，通过。
- `npm run test:e2e`，通过，1 个 `StarletteDeprecationWarning`。
- `npm run eval:standard`，20/20 链路成功，严格成功率 55%。

风险/后续：

- 当前 batch 失败会让该 batch 内记录全部失败；后续可补 batch 失败后的单条重试。
- 本模块不实现并发、限速或后台队列。
