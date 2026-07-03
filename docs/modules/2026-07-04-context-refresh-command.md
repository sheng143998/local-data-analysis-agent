# 模块：数据上下文刷新命令

当前状态：本模块已完成服务、CLI、脚本入口、focused tests、完整验证和文档更新，已提交并推送。它不新增固定 SQL 模板，不改变普通用户前端，不改变 `/api/analyze` 响应。

业务逻辑：当用户换库、导入新表或调整字段后，系统需要先刷新真实表结构，再刷新 schema、metric、SQL Memory 的 embedding。统一命令降低人工漏跑步骤的概率，让后续检索和模型 SQL 生成更依赖真实数据库上下文，而不是固定模板。

关键代码：

- `backend/app/services/context_refresh_service.py`：新增 `ContextRefreshService`，按顺序调用 `SchemaSyncService` 和 `EmbeddingSyncService`。
- `backend/scripts/refresh_context.py`：新增 CLI，支持 `--include-table`、`--exclude-table`、`--skip-embeddings` 和 `--embedding-target`。
- `backend/tests/test_context_refresh_service.py`：覆盖默认全量刷新、跳过 embedding、指定 target 和非法 target。
- `package.json`：新增 `npm run context:refresh`。

数据契约：

- 不新增 API 字段。
- `ContextRefreshResult.schema_result` 记录 schema 扫描和同步结果。
- `ContextRefreshResult.embedding_results` 记录各 embedding target 的扫描、更新、失败和错误摘要。

验证：

- `py -3 -m pytest backend/tests/test_context_refresh_service.py`，4 passed。
- `npm run backend:test`，115 passed，1 个 `StarletteDeprecationWarning`。
- `npm run frontend:build`，通过。
- `npm run test:e2e`，通过，1 个 `StarletteDeprecationWarning`。
- `py -3 backend/scripts/refresh_context.py --help`，通过。
- `npm run eval:standard`，20/20 链路成功，严格成功率 55%。

风险/后续：

- embedding 质量仍取决于当前 `EMBEDDING_PROVIDER` 配置；本地 deterministic fallback 只能保证可运行和稳定测试。
- 本模块是手动刷新命令，不包含数据库变更监听、定时任务或后台队列。
