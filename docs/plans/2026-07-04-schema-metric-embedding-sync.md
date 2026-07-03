# Schema / Metric Embedding 同步计划

## Goal

本模块把 `schema_metadata` 和 `metric_definitions` 中的可检索文本生成 embedding，并写回 pgvector 字段，推动 schema/metric 从纯关键词召回走向混合检索。它不新增固定 SQL 模板，不改变普通用户界面，不展示模型或向量状态。

## Current task

当前正在做：补齐同步脚本、单元测试、文档和验证。

## Scope

包含：

- 新增 `backend/app/services/embedding_sync_service.py`。
- 生成 schema 字段文档和 metric 指标文档。
- 调用 `EmbeddingAdapter` 生成向量。
- 回写：
  - `schema_metadata.embedding`
  - `metric_definitions.embedding`
- 新增 `backend/scripts/sync_embeddings.py`。
- 增加 focused tests。
- 更新 README、handoff 和模块完成说明。

不包含：

- 不接入实际 pgvector 查询排序。
- 不改 `/api/analyze` 主链路。
- 不修改数据库 migration。
- 不新增 SQL 模板。
- 不在普通用户前端展示 embedding provider、模型或数据库连接状态。

## Module boundary

上游输入：

- `schema_metadata` 的 `table_name`、`column_name`、`data_type`、`description`、`business_meaning`。
- `metric_definitions` 的 `metric_name`、`display_name`、`description`、`formula`、`required_tables`、`required_fields`、`default_filters`。
- `EmbeddingAdapter`。

下游输出：

- pgvector 字段字符串 literal，例如 `[0.1,0.2,0.3]`，通过 `%s::vector` 写入数据库。
- `EmbeddingSyncResult`，记录同步条数和失败信息。

预计触达文件：

- `backend/app/services/embedding_sync_service.py`
- `backend/scripts/sync_embeddings.py`
- `backend/tests/test_embedding_sync_service.py`
- `README.md`
- `docs/handoff/current.md`
- `docs/modules/2026-07-04-schema-metric-embedding-sync.md`

## Business logic

换库或新增表字段后，业务人员不应该依赖固定模板才能提问。系统需要把字段说明和指标口径变成可向量检索的文本资产。本模块先实现同步写入，后续再在 retriever 中把 pgvector 查询纳入混合检索。

## Data contract

`EmbeddingSyncResult`：

- `target`: `schema` 或 `metric`
- `scanned`: 扫描记录数
- `updated`: 成功写入 embedding 数
- `failed`: 失败数
- `errors`: 错误摘要

脚本：

```bash
py -3 backend/scripts/sync_embeddings.py
py -3 backend/scripts/sync_embeddings.py --target schema
py -3 backend/scripts/sync_embeddings.py --target metric
```

## Implementation steps

- [x] 读取 handoff、EmbeddingAdapter、数据库连接和 schema sync 代码。
- [x] 实现 `EmbeddingSyncService`。
- [x] 新增同步脚本。
- [x] 增加单元测试。
- [x] 更新文档和模块完成说明。
- [x] 运行验证。
- [x] commit 并 push。

## Validation plan

- `npm run backend:test`，94 passed，1 个 `StarletteDeprecationWarning`
- `npm run frontend:build`，通过
- `npm run test:e2e`，通过，1 个 `StarletteDeprecationWarning`

本模块不修改前端和 analyze 语义，暂不强制运行 `npm run eval:standard`。

## Risks and open questions

- 默认 deterministic embedding 不是语义向量，只是本地 fallback；真实检索质量需要配置真实 embedding provider。
- 当前只同步 schema 和 metric，SQL Memory question/sql embedding 后续单独做。
- 写入 pgvector 后，retriever 仍需后续模块接入向量查询。
