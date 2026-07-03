# Schema 字段业务含义提示计划

## Goal

当前 `SchemaSyncService` 会把新字段写入 `schema_metadata`，但默认说明基本只是 `业务表字段：table.column`，对 schema 检索、embedding 文档和模型 SQL prompt 的帮助有限。换库或新增表后，如果没有人工维护说明，系统应先根据字段命名生成基础中文业务含义，提升通用检索质量，而不是继续增加固定 SQL 模板。

## Current task

当前正在做：本模块已完成实现、测试、文档更新、commit 和 push。

## Scope

包含：

- 根据字段名和数据类型生成默认 `description`。
- 根据字段名和数据类型生成默认 `business_meaning`。
- 覆盖常见通用字段：`id`、`*_id`、时间字段、状态字段、金额字段、数量字段、城市/地区、类型、名称、评分、原因等。
- 保留已有 `description` / `business_meaning` 的行为不变。
- 更新测试、README/数据模型或 schema 同步文档、handoff 和模块完成说明。

不包含：

- 不调用外部模型。
- 不新增固定 SQL 模板。
- 不改变普通用户前端。
- 不覆盖已有人工字段说明。

## Module boundary

上游输入：

- `SchemaColumnSnapshot.table_name`
- `SchemaColumnSnapshot.column_name`
- `SchemaColumnSnapshot.data_type`

下游输出：

- `schema_metadata.description`
- `schema_metadata.business_meaning`
- 后续 `build_schema_embedding_document()` 使用的 schema 文档文本。

预计触达文件：

- `backend/app/services/schema_sync_service.py`
- `backend/tests/test_schema_sync_service.py`
- `README.md`
- `docs/data_model.md`
- `docs/handoff/current.md`
- `docs/modules/2026-07-04-schema-business-meaning-hints.md`

## Business logic

当开发者换库、导入新表或新增字段后，运行 `sync_schema_metadata.py` 或 `context:refresh` 时，新字段会获得比裸字段名更有帮助的中文说明。例如：

- `orders.total_amount` -> 金额字段，用于金额汇总、客单价或交易规模分析。
- `orders.user_id` -> 关联用户表或用户实体的外键。
- `users.city` -> 城市维度字段，可用于地域分组分析。

## Data contract

数据库字段不变，增强写入内容：

- `schema_metadata.description`
- `schema_metadata.business_meaning`

人工说明保留策略不变：

- 仅当已有值为空字符串时，用本次推断值补齐。

## Implementation steps

- [x] 读取 handoff、schema sync、embedding sync 和相关测试。
- [x] 创建计划文档。
- [x] 实现字段含义推断 helper。
- [x] 更新 focused tests。
- [x] 更新文档、handoff 和模块完成说明。
- [x] 运行验证。
- [x] commit 并 push。

## Validation plan

- `py -3 -m pytest backend/tests/test_schema_sync_service.py backend/tests/test_embedding_sync_service.py`
- `npm run backend:test`
- `npm run eval:standard`
- `npm run frontend:build`
- `npm run test:e2e`

## Risks and open questions

- 字段名启发式不能替代人工业务口径，后续仍应允许用户编辑 schema 说明。
- 非英文或非常规字段名只能生成通用说明，后续可结合本地模型做离线补全。
