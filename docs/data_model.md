# V1 数据模型说明

## 数据库

当前使用本地 PostgreSQL：

```text
database: local_data_agent
schema: public
```

真实连接串只保存在 `backend/.env`，示例配置保存在 `backend/.env.example`。

## 业务表

Olist 真实数据和合成增强表包括：

- `users`：用户基础信息，含城市等维度。
- `products`：商品基础信息和品类。
- `orders`：订单主表，含用户、时间、订单金额。
- `order_items`：订单商品明细。
- `payments`：支付记录，含支付方式、金额和状态。
- `refunds`：退款记录。
- `reviews`：评价记录。
- `traffic_events`：访问、加购等合成流量事件。
- `coupons`：优惠券。
- `coupon_usages`：优惠券使用记录。
- `inventory_snapshots`：库存快照。
- `product_costs`：商品成本，用于毛利率。

## Agent 元数据表

- `schema_metadata`：表字段说明，用于 Schema Retriever；新增或空说明字段会由 schema 同步按字段名生成基础中文业务含义；`embedding` 字段用于 pgvector 语义候选召回。
- `metric_definitions`：指标口径，支持 API CRUD；`embedding` 字段用于 pgvector 语义候选召回。
- `sql_memories`：历史成功问题、SQL、参数、表、指标和复用统计；`question_embedding` / `sql_embedding` 用于 SQL Memory 混合检索。
- `query_runs`：每次分析运行记录。
- `tool_calls`：每次工具调用摘要。
- `embedding_documents`：后续 RAG 文档和 embedding 存储。

## 后端内部检索上下文

- `RetrievalContext.metrics`：本次问题召回的指标口径。
- `RetrievalContext.schema_columns`：本次问题召回的字段上下文。
- `RetrievalContext.table_relationships`：从已召回字段推断出的表关系提示，例如 `orders.id = payments.order_id`。该字段只用于后端 SQL Generator prompt，不写入数据库，也不展示给普通用户。
- `RetrievalContext.tables` / `fields`：本次 SQL 生成允许使用的表和字段。

## 迁移脚本

迁移位于 `backend/app/db/migrations/`：

- `001_extensions.sql`：pgvector、pg_trgm 等扩展。
- `002_business_tables.sql`：业务表。
- `003_agent_metadata.sql`：Agent 元数据表和索引。
- `004_schema_metadata_unique.sql`：`schema_metadata(table_name, column_name)` 唯一索引。

初始化：

```bash
py -3 backend/scripts/init_db.py
```

同步 schema metadata：

```bash
py -3 backend/scripts/sync_schema_metadata.py
```

schema 同步会保留已有人工 `description` / `business_meaning`，只在字段说明为空时写入自动推断的基础含义。

同步 schema/metric/SQL Memory embedding：

```bash
py -3 backend/scripts/sync_embeddings.py
py -3 backend/scripts/sync_embeddings.py --target memory
py -3 backend/scripts/sync_embeddings.py --target memory --limit 20
py -3 backend/scripts/sync_embeddings.py --target schema --limit 100 --batch-size 16
py -3 backend/scripts/sync_embeddings.py --target schema --limit 100 --batch-size 16 --sleep-ms 200
```

`--limit` 是每个目标本次同步的记录数上限，适合在真实 embedding provider 配置后先小批量验证。`--batch-size` 控制每次 embedding 请求包含的记录数，用于降低真实 provider 请求次数。`--sleep-ms` 控制连续请求之间的固定等待时间，用于降低限流风险。

## 指标口径

指标 CRUD API：

- `GET /api/metrics`
- `POST /api/metrics`
- `PUT /api/metrics/{metric_id}`
- `DELETE /api/metrics/{metric_id}`

`metric_definitions` 字段包括指标名、展示名、说明、公式、依赖表、依赖字段、默认过滤、示例问题、负责人和状态。

## 当前风险

- 测试直接使用本地库，尚未隔离测试数据库。
- `product_costs.unit_cost` 是合成成本。
- `traffic_events`、`coupons`、`coupon_usages` 的语义评估仍在增强中。
- schema/metric 和 SQL Memory 已接入 pgvector 混合检索；真实质量依赖 embedding provider 和历史记录是否已写入向量。
