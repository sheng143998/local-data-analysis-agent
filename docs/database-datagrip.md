# DataGrip 连接说明

当前脚本实际初始化的 PostgreSQL 位置：

```text
host: 127.0.0.1
port: 5432
database: local_data_agent
user: postgres
schema: public
```

注意：用户最初提供的 `postgre` 认证失败，本机实际可用用户名是 `postgres`。

## DataGrip 看不到表时检查

1. 确认连接的是 `local_data_agent`，不是默认的 `postgres` 数据库。
2. 确认用户是 `postgres`。
3. 在 DataGrip 左侧连接上右键，选择刷新。
4. 展开：

```text
local_data_agent
  schemas
    public
      tables
```

5. 如果仍然看不到，运行：

```bash
py -3 backend/scripts/check_db.py
```

当前脚本确认的表包括：

```text
users
products
orders
order_items
payments
refunds
reviews
traffic_events
coupons
coupon_usages
inventory_snapshots
product_costs
schema_metadata
metric_definitions
sql_memories
query_runs
tool_calls
embedding_documents
```
