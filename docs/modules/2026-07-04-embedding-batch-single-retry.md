# 模块：Embedding 批量失败单条重试

当前状态：本模块已完成服务、focused tests、完整验证和文档更新，等待 commit 和 push。它不新增固定 SQL 模板，不改变普通用户前端，不改变 `/api/analyze` 主链路。

业务逻辑：同步 schema、metric 和 SQL Memory embedding 时，系统优先使用 batch 请求降低真实 provider 请求次数。如果某个 batch 失败或返回向量数量不足，会自动退回单条重试，让同批次中可成功的记录继续写回，只把真正失败的记录计入错误摘要。

关键代码：

- `backend/app/services/embedding_sync_service.py`：schema、metric、memory 和 all 同步入口新增 `retry_single_on_batch_failure`，默认开启。
- `EmbeddingSyncService._retry_schema_records()`：schema batch 失败后的单条重试。
- `EmbeddingSyncService._retry_metric_records()`：metric batch 失败后的单条重试。
- `EmbeddingSyncService._retry_sql_memory_records()`：SQL Memory batch 失败后的问题/SQL 成对单条重试。
- `backend/app/services/context_refresh_service.py`：透传 `retry_single_on_batch_failure`。
- `backend/tests/test_embedding_sync_service.py`：覆盖 schema、metric、memory 的 batch 失败单条重试。
- `backend/tests/test_context_refresh_service.py`：覆盖刷新服务透传重试开关。

数据契约：

- 不新增 API 字段。
- 内部服务新增可选参数 `retry_single_on_batch_failure: bool = True`。
- `EmbeddingSyncResult.scanned/updated/failed/errors` 语义保持不变。

验证：

- `py -3 -m pytest backend/tests/test_embedding_sync_service.py backend/tests/test_context_refresh_service.py`，28 passed。
- `npm run backend:test`，129 passed，1 个 `StarletteDeprecationWarning`。
- `npm run frontend:build`，通过。
- `npm run test:e2e`，通过，1 个 `StarletteDeprecationWarning`。
- `npm run eval:standard`，20/20 链路成功，严格成功率 55%。

风险/后续：

- 单条重试只在 batch 失败时触发，失败 batch 会增加请求次数。
- 仍未实现 provider 级限速、后台队列或断点游标。
