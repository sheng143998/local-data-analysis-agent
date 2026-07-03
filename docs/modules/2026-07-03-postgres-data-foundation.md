# 模块完成说明：PostgreSQL 数据库与真实 Olist 数据基础

模块：PostgreSQL 数据库与真实 Olist 数据基础

当前状态：已完成，已导入真实 Olist 数据，已提交并推送。当前数据库为 `local_data_agent`，schema 为 `public`。

业务逻辑：
- 为本地数据分析 Agent 建立真实数据基础。
- 使用 Olist 公开电商数据作为交易、订单、支付、评价、商品、用户数据来源。
- 生成退款、商品成本、库存快照等增强分析表。
- 为后续 SQL 生成、Schema Retriever、Metric Retriever、SQL Executor 提供真实表结构和数据。

关键代码：
- `backend/app/db/connection.py`：读取 `DATABASE_URL` 并创建 PostgreSQL 连接。
- `backend/app/db/migrations/001_extensions.sql`：启用 `vector` 和 `pg_trgm`。
- `backend/app/db/migrations/002_business_tables.sql`：创建业务表。
- `backend/app/db/migrations/003_agent_metadata.sql`：创建 Agent 元数据表。
- `backend/scripts/init_db.py`：创建数据库并执行 migrations。
- `backend/scripts/download_olist.py`：下载 Olist CSV。
- `backend/scripts/import_olist.py`：导入 Olist 数据并生成增强表。
- `backend/scripts/seed_metadata.py`：写入指标口径和 schema metadata。
- `backend/scripts/check_db.py`：检查核心表行数。

数据契约：
- Database: `local_data_agent`
- Schema: `public`
- 业务表：`users`, `products`, `orders`, `order_items`, `payments`, `refunds`, `reviews`, `traffic_events`, `coupons`, `coupon_usages`, `inventory_snapshots`, `product_costs`
- 元数据表：`schema_metadata`, `metric_definitions`, `sql_memories`, `query_runs`, `tool_calls`, `embedding_documents`

验证：
- `py -3 backend/scripts/init_db.py`
- `py -3 backend/scripts/download_olist.py`
- `py -3 backend/scripts/import_olist.py`
- `py -3 backend/scripts/seed_metadata.py`
- `py -3 backend/scripts/check_db.py`
- `npm run backend:test`
- `npm run test:e2e`
- `npm run frontend:build`

风险/后续：
- 当前 `metric_definitions` 已入库，但 `/api/metrics` 仍使用内存 repository。
- 下一步需要将指标 CRUD 切换为 PostgreSQL repository。
- 当前导入脚本是全量导入，后续可以增加更严格的幂等策略和导入进度记录。
