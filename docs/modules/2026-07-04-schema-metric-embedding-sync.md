# 模块：Schema / Metric Embedding 同步

当前状态：本模块已完成代码、测试和文档更新，并通过全量验证，随本次提交推送完成。它不改普通用户前端，不接入 `/api/analyze` 主链路，也不新增固定 SQL 模板。

业务逻辑：换库、导入新表或维护指标口径后，系统可以把字段说明和指标口径转换成 embedding 并写回 pgvector 字段。业务用户不需要看到向量、模型或数据库状态；这些资产只服务于后续自动检索。

关键代码：

- `backend/app/services/embedding_sync_service.py`：读取 `schema_metadata` 和启用状态的 `metric_definitions`，构造中文业务文档，调用 `EmbeddingAdapter.embed()`，并通过 `%s::vector` 写回 PostgreSQL。
- `backend/scripts/sync_embeddings.py`：命令行入口，支持 `--target all|schema|metric`。
- `backend/tests/test_embedding_sync_service.py`：用 fake connection 和 fake adapter 覆盖文档构造、向量 literal、JSON 容错、schema/metric 回写和失败不中断。

数据契约：

- `schema_metadata.embedding`: schema 字段文档向量。
- `metric_definitions.embedding`: 指标口径文档向量。
- `EmbeddingSyncResult`: `target`、`scanned`、`updated`、`failed`、`errors`。

验证：

- `py -3 -m pytest backend/tests/test_embedding_sync_service.py`，7 passed。
- `npm run backend:test`，94 passed，1 个 `StarletteDeprecationWarning`。
- `npm run frontend:build`，通过。
- `npm run test:e2e`，通过，1 个 `StarletteDeprecationWarning`。

风险/后续：

- deterministic embedding 只用于本地开发和测试，不代表真实语义检索质量。
- 本模块只负责写入向量，后续还要把 pgvector 查询接入 schema、metric、SQL Memory 的混合检索。
- SQL Memory 的 question/sql embedding 后续单独实现。
