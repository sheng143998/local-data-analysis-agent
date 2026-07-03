# PostgreSQL 数据库与真实数据采集计划

Goal: 建立真实 PostgreSQL 数据基础，补齐业务表迁移、数据库初始化脚本、Olist 真实数据采集脚本和本地 `.env` 配置。

当前正在做：模块已完成，PostgreSQL 数据库已初始化，真实 Olist 数据已下载并导入，验证已通过。

Scope:
- 包含：`.env` 本地配置、requirements 更新、数据库连接、migration runner、业务表建表、Olist 数据下载脚本、CSV 导入脚本、数据库 smoke 测试。
- 不包含：完整生产级 ETL、增量同步、真实 embedding 写入、所有分析增强表的大规模合成数据。

Module boundary:
- Upstream inputs: PostgreSQL 连接信息、Olist 公开数据集 CSV、migration SQL。
- Downstream outputs: PostgreSQL 数据库、业务表、Agent 元数据表、可重复运行的初始化/导入命令。
- Likely touched files: `backend/.env`, `backend/requirements.txt`, `backend/app/db`, `backend/app/data`, `backend/scripts`, `backend/tests`, `docs/handoff/current.md`。

Business logic:
- 本地数据分析 Agent 需要真实业务数据承载 SQL 查询。
- V1 使用 Olist 公开电商数据作为真实交易数据基础。
- 后续 SQL Generator、SQL Executor、指标口径和 SQL Memory 都依赖这些表结构和数据。

Data contract:
- Database: `local_data_agent`
- Business tables: `users`, `products`, `orders`, `order_items`, `payments`, `refunds`, `reviews`, `traffic_events`, `coupons`, `coupon_usages`, `inventory_snapshots`, `product_costs`
- Agent metadata tables: `schema_metadata`, `metric_definitions`, `sql_memories`, `query_runs`, `tool_calls`, `embedding_documents`

Implementation steps:
- [x] 创建模块计划
- [x] 创建本地 `.env`
- [x] 添加 PostgreSQL 连接和 migration runner
- [x] 添加业务表和 Agent 元数据 migrations
- [x] 添加 Olist 数据下载脚本
- [x] 添加 Olist CSV 导入脚本
- [x] 添加数据库 smoke 测试
- [x] 运行初始化和验证
- [x] 更新 handoff
- [x] commit 并 push

Validation plan:
- `py -3 backend/scripts/init_db.py`
- `py -3 backend/scripts/download_olist.py --limit-check`
- `npm run backend:test`
- `npm run test:e2e`

Risks and open questions:
- Olist 原始数据已从公开 GitHub raw 镜像下载成功。
- 用户提供的 `postgre` 用户认证失败；实际可用账号为 `postgres` / `123456`，本地 `.env` 已按可用账号配置。
- 当前导入脚本是全量 CSV 导入，后续需要做幂等增强和更完整的增强表数据生成。
