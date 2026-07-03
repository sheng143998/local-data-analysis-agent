# Schema Metadata 自动同步完成说明

模块：Schema Metadata 自动同步

当前状态：已完成实现、验证和文档更新，等待提交并推送到 GitHub。

业务逻辑：

- 当本地 PostgreSQL 换库、导入新表或字段发生变化后，开发者运行 `py -3 backend/scripts/sync_schema_metadata.py`。
- 系统从 `information_schema.columns` 扫描当前 `public` schema 下的真实业务表字段。
- 同步结果 upsert 到 `schema_metadata`，让后续 Schema Retriever、SQL Memory 和动态 SQL 生成链路使用最新表结构。
- 同步时保留已有人工 `description` 和 `business_meaning`，只给新增或空说明字段生成默认中文说明。
- 普通用户界面不展示数据库连接状态或同步细节，只消费同步后的可信 schema 上下文。

关键代码：

- `backend/app/services/schema_sync_service.py`
  - 新增 `SchemaSyncService.sync_public_schema()`，支持 `include_tables` 和 `exclude_tables`。
  - 默认排除 Agent 元数据表：`schema_metadata`、`metric_definitions`、`sql_memories`、`query_runs`、`tool_calls`、`embedding_documents`。
  - 新增 `SchemaColumnSnapshot` 和 `SchemaSyncResult`，让同步结果可测试、可打印。
- `backend/scripts/sync_schema_metadata.py`
  - 新增命令脚本，读取 `backend/.env` 后执行 schema 同步并打印同步表清单。
- `backend/scripts/seed_metadata.py`
  - 复用 `SchemaSyncService`，避免 seed 脚本和同步脚本各自维护一套 schema 写入逻辑。
- `backend/app/db/migrations/004_schema_metadata_unique.sql`
  - 先清理重复 `(table_name, column_name)` 元数据，再创建唯一索引。
  - 为 `ON CONFLICT (table_name, column_name)` 提供数据库约束保障。
- `backend/tests/test_schema_sync_service.py`
  - 覆盖过滤条件、字段快照加载和 upsert 保留人工说明逻辑。

数据契约：

- 写入表：`schema_metadata`
- 唯一键：`table_name + column_name`
- 同步字段：`table_name`、`column_name`、`data_type`、`description`、`business_meaning`、`updated_at`
- 输出结果：`SchemaSyncResult.scanned_columns`、`synced_columns`、`tables`

验证：

- `npm run backend:test`：54 passed，1 个 `StarletteDeprecationWarning`。
- `py -3 backend/scripts/init_db.py`：迁移 001-004 均成功应用。
- `py -3 backend/scripts/sync_schema_metadata.py`：同步 12 张业务表、78 个字段。
- `npm run test:e2e`：通过，完成 question -> FastAPI -> AgentService -> Guard -> Executor -> result smoke。
- `npm run frontend:build`：通过，Vite 生产构建成功。

风险/后续：

- 本模块只解决字段结构同步，不自动生成业务指标口径；指标仍通过指标 CRUD 或后续 RAG 文档补充。
- embedding 暂未写入，后续需要接统一 embedding adapter 和 pgvector 混合召回。
- 当前同步范围默认排除 Agent 元数据表，若未来需要分析系统运行表，应显式调整 include/exclude 策略。
