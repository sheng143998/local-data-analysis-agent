# 模块：Schema 历史泛化说明刷新

当前状态：本模块已完成显式刷新开关、完整验证、commit 和 push。提交信息为 `新增Schema历史泛化说明刷新并通过验证`，已推送到 GitHub。它不新增固定 SQL 模板，不调用外部模型，不改变普通用户前端。

业务逻辑：早期 `schema_metadata` 中可能已经存在 `orders.created_at`、`业务表字段：orders.created_at` 这类系统泛化说明。因为它们不是空值，上一模块不会自动更新。本模块新增 `--refresh-generated-descriptions`，开发者显式开启后，只刷新这些已知系统生成格式，人工维护的字段说明不被覆盖。

关键代码：

- `backend/app/services/schema_sync_service.py`
  - `sync_public_schema(..., refresh_generated_descriptions=False)`：新增显式刷新参数。
  - `_upsert_schema_metadata(..., refresh_generated_descriptions=False)`：开启时允许替换旧自动生成说明。
- `backend/app/services/context_refresh_service.py`
  - `refresh(..., refresh_generated_descriptions=False)`：透传到 schema sync。
- `backend/scripts/sync_schema_metadata.py`
  - 新增 `--include-table`、`--exclude-table` 和 `--refresh-generated-descriptions` 参数。
- `backend/scripts/refresh_context.py`
  - 新增 `--refresh-generated-descriptions` 参数。
- `backend/tests/test_schema_sync_service.py`
  - 覆盖默认保守行为和显式刷新行为。
- `backend/tests/test_context_refresh_service.py`
  - 覆盖 context refresh 参数透传。

数据契约：

- `SchemaSyncService.sync_public_schema(refresh_generated_descriptions: bool = False)`
- `ContextRefreshService.refresh(refresh_generated_descriptions: bool = False)`
- CLI：`--refresh-generated-descriptions`

验证：

- `py -3 -m pytest backend/tests/test_schema_sync_service.py backend/tests/test_context_refresh_service.py`，10 passed。
- `py -3 backend/scripts/sync_schema_metadata.py --help` 已通过。
- `py -3 backend/scripts/refresh_context.py --help` 已通过。
- `npm run backend:test`，142 passed，1 个 `StarletteDeprecationWarning`。
- `npm run eval:standard`，20/20 链路成功，严格成功率 55%。
- `npm run frontend:build` 已通过。
- `npm run test:e2e` 已通过，1 个 `StarletteDeprecationWarning`。

风险/后续：

- 只识别当前已知的旧自动生成格式；如果历史数据里有其他格式，后续可补数据修复脚本。
- 刷新 schema 说明后应同步 schema embedding，才能让 pgvector 检索用到新文本。
