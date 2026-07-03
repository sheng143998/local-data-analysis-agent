# 模块：Embedding 同步批次限速

当前状态：本模块已完成服务、CLI、focused tests、完整验证和文档更新，等待 commit 和 push。它不新增固定 SQL 模板，不改变普通用户前端，不改变 `/api/analyze` 主链路。

业务逻辑：真实 embedding provider 可能有 QPS 或 RPM 限制。开发者同步 schema、metric 和 SQL Memory embedding 时，可以通过 `sleep_ms` 在连续请求之间增加固定等待，降低限流失败概率。默认值为 `0`，保持当前速度。

关键代码：

- `backend/app/services/embedding_sync_service.py`：同步入口新增 `sleep_ms`；支持注入 `sleeper`，测试不会真实等待。
- `EmbeddingSyncService._sleep_between_requests()`：统一处理毫秒到秒的转换和等待。
- `backend/app/services/context_refresh_service.py`：新增 `embedding_sleep_ms` 并透传。
- `backend/scripts/sync_embeddings.py`：新增 `--sleep-ms`。
- `backend/scripts/refresh_context.py`：新增 `--embedding-sleep-ms`。
- `backend/tests/test_embedding_sync_service.py`：覆盖 sleep 参数、批次间等待和单条重试等待。
- `backend/tests/test_context_refresh_service.py`：覆盖刷新服务透传 `sleep_ms`。

数据契约：

- 不新增 API 字段。
- 内部服务新增可选参数 `sleep_ms: int = 0`。
- CLI 新增 `--sleep-ms` / `--embedding-sleep-ms`。
- `EmbeddingSyncResult.scanned/updated/failed/errors` 语义保持不变。

验证：

- `py -3 -m pytest backend/tests/test_embedding_sync_service.py backend/tests/test_context_refresh_service.py`，32 passed。
- `py -3 backend/scripts/sync_embeddings.py --help`，通过。
- `py -3 backend/scripts/refresh_context.py --help`，通过。
- `npm run backend:test`，133 passed，1 个 `StarletteDeprecationWarning`。
- `npm run frontend:build`，通过。
- `npm run test:e2e`，通过，1 个 `StarletteDeprecationWarning`。
- `npm run eval:standard`，20/20 链路成功，严格成功率 55%。

风险/后续：

- 当前是固定等待，不是基于 provider 响应码的自适应退避。
- 仍未实现后台队列、断点游标和自动恢复。
