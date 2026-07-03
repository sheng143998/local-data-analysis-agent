# Schema 历史泛化说明刷新计划

## Goal

上一模块让新增或空说明字段能生成更好的中文业务含义，但历史 `schema_metadata` 中已有的泛化说明（如 `orders.created_at`、`业务表字段：orders.created_at`）不是空值，默认不会被更新。本模块新增显式刷新开关，只替换系统生成的泛化说明，保留人工维护说明，提升已有库的 schema 检索和 embedding 文档质量。

## Current task

当前正在做：本模块已完成实现、测试、文档更新、commit 和 push。

## Scope

包含：

- `SchemaSyncService.sync_public_schema()` 增加 `refresh_generated_descriptions` 参数。
- 开启后替换早期系统生成的泛化 `description` / `business_meaning`。
- 默认保持现有保守行为，不覆盖非空说明。
- `sync_schema_metadata.py` 和 `refresh_context.py` 增加 CLI 参数。
- `ContextRefreshService.refresh()` 透传该参数。
- 更新测试、README、数据模型、handoff 和模块说明。

不包含：

- 不覆盖人工维护的 schema 说明。
- 不调用外部模型。
- 不新增固定 SQL 模板。
- 不改变普通用户前端。

## Module boundary

上游输入：

- `refresh_generated_descriptions: bool`
- 当前 PostgreSQL `information_schema.columns`
- 当前 `schema_metadata.description` / `business_meaning`

下游输出：

- 仅在字段说明为空或匹配早期系统泛化说明时，写入新的推断说明。

预计触达文件：

- `backend/app/services/schema_sync_service.py`
- `backend/app/services/context_refresh_service.py`
- `backend/scripts/sync_schema_metadata.py`
- `backend/scripts/refresh_context.py`
- `backend/tests/test_schema_sync_service.py`
- `backend/tests/test_context_refresh_service.py`
- `README.md`
- `docs/data_model.md`
- `docs/handoff/current.md`
- `docs/modules/2026-07-04-schema-generated-description-refresh.md`

## Business logic

开发者希望升级历史字段说明时，可以运行：

```bash
py -3 backend/scripts/sync_schema_metadata.py --refresh-generated-descriptions
```

或：

```bash
npm run context:refresh -- --refresh-generated-descriptions
```

系统只会更新空说明或早期自动生成的泛化说明，人工写过的字段说明不会被覆盖。

## Data contract

新增服务参数：

- `SchemaSyncService.sync_public_schema(refresh_generated_descriptions: bool = False)`
- `ContextRefreshService.refresh(refresh_generated_descriptions: bool = False)`

新增 CLI 参数：

- `--refresh-generated-descriptions`

## Implementation steps

- [x] 读取 handoff、schema sync、context refresh 和脚本入口。
- [x] 创建计划文档。
- [x] 实现服务参数和 SQL upsert 条件。
- [x] 更新脚本和 context refresh 透传。
- [x] 更新 focused tests。
- [x] 更新文档、handoff 和模块完成说明。
- [x] 运行验证。
- [x] commit 并 push。

## Validation plan

- `py -3 -m pytest backend/tests/test_schema_sync_service.py backend/tests/test_context_refresh_service.py`
- `py -3 backend/scripts/sync_schema_metadata.py --help`
- `py -3 backend/scripts/refresh_context.py --help`
- `npm run backend:test`
- `npm run eval:standard`
- `npm run frontend:build`
- `npm run test:e2e`

## Risks and open questions

- 系统只能识别已知泛化说明格式；非常早期或人工复制的类似说明可能需要后续数据修复脚本。
- 开启刷新后应重新同步 schema embedding，才能让 pgvector 语义检索用到更新后的文本。
