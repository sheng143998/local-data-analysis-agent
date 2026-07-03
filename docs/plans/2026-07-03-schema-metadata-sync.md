# Schema Metadata 自动同步计划

当前正在做：Schema Metadata 自动同步模块已完成实现、验证和文档更新，等待提交并推送。

## Goal

当用户切换或调整本地数据库表结构后，系统可以重新扫描 `information_schema.columns`，把可分析表字段同步到 `schema_metadata`，让后续 Schema Retriever、SQL Memory 和动态 SQL 生成链路基于最新表结构工作。

## Scope

- 包含：
  - 增加 `schema_metadata(table_name, column_name)` 唯一约束。
  - 新增 schema 同步服务，支持指定 include/exclude 表。
  - 新增命令脚本 `backend/scripts/sync_schema_metadata.py`。
  - 更新 seed 脚本复用同步服务。
  - 增加同步逻辑测试。
  - 更新 README、模块说明和 handoff。
- 不包含：
  - 新增业务问题固定 SQL 模板。
  - 真实 embedding 写入。
  - 通用 LLM SQL Generator 接入。

## Module Boundary

- 上游输入：当前 PostgreSQL `public` schema 下的真实表结构。
- 核心处理：读取 `information_schema.columns`，upsert 到 `schema_metadata`。
- 下游输出：Schema Retriever 可读取最新表字段上下文。

## Business Logic

- 系统管理员或开发者在换库、导入新表、修改字段后运行同步脚本。
- 同步会保留已有人工说明，并只为新增字段生成默认中文说明。
- 业务用户页面不展示数据库连接状态或同步细节，普通问答链路只消费同步后的 schema 上下文。

## Data Contract

- `schema_metadata.table_name`
- `schema_metadata.column_name`
- `schema_metadata.data_type`
- `schema_metadata.description`
- `schema_metadata.business_meaning`
- `schema_metadata.updated_at`

## Implementation Steps

任务清单：
- [x] 创建计划文档。
- [x] 实现 schema 同步服务、脚本和迁移。
- [x] 增加聚焦测试。
- [x] 更新 README、模块完成文档和 handoff。
- [~] 运行验证并提交推送。

## Validation Plan

- `npm run backend:test`
- `npm run test:e2e`
- `npm run frontend:build`

## Risks and Open Questions

- 本模块只同步字段结构，不自动理解业务口径；业务含义仍需指标 CRUD 或后续 RAG 文档补充。
- embedding 暂未写入，后续需要接统一 embedding adapter。
