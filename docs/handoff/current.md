# 当前 Handoff

## 当前状态

- 项目已连接 GitHub：`https://github.com/sheng143998/local-data-analysis-agent`
- 当前分支：`main`
- 前后端目录已拆分：
  - `frontend/`: React + Vite + TypeScript 前端
  - `backend/`: FastAPI 后端
  - `docs/`: 草案、计划、handoff
- 当前普通用户产品方向：聊天式数据问答 + 指标口径 CRUD，不默认展示模型、数据库连接状态、SQL 记忆细节和评估报告。
- `/api/analyze` 已接入 PostgreSQL 指标口径和表结构上下文召回，当前仍使用固定销售趋势 SQL 模板。
- `/api/analyze` 已写入 `query_runs` 和 `tool_calls`，开发者可通过 `/api/runs` 查看运行记录。

## 最近完成模块

### 1. 项目结构与 FastAPI 最小闭环

- commit: `8071783 初始化项目结构并通过前后端验证`
- 内容：
  - 创建 `frontend/` 和 `backend/`
  - FastAPI mock `/api/analyze`
  - 前端聊天式问答页
  - 根目录项目脚本
- 验证：
  - `npm run frontend:build`
  - `npm run backend:test`
  - `npm run test:e2e`

### 2. 指标口径后端 CRUD

- commit: `094ecf2 实现指标口径后端CRUD并通过测试`
- 内容：
  - `GET/POST/PUT/DELETE /api/metrics`
  - `MetricService`
  - 内存版 `MetricRepository`
  - `metric_definitions` migration
  - 前端指标页接入 `metricClient`
- 验证：
  - `npm run backend:test`，3 个测试通过
  - `npm run frontend:build`
  - `npm run test:e2e`

### 3. PostgreSQL 数据库与真实 Olist 数据基础

- commit: 本模块已提交并推送，提交信息为 `建立PostgreSQL数据基础并导入真实Olist数据`。具体 hash 以 `git log --oneline -1` 为准。
- 内容：
  - 创建本地 `backend/.env`，使用可连接账号 `postgres` / `123456` 指向 `local_data_agent`
  - 添加 PostgreSQL 连接、migration runner、Olist 下载脚本、Olist 导入脚本、metadata seed 和数据库检查脚本
  - 创建业务表：`users`, `products`, `orders`, `order_items`, `payments`, `refunds`, `reviews`, `traffic_events`, `coupons`, `coupon_usages`, `inventory_snapshots`, `product_costs`
  - 创建 Agent 元数据表：`schema_metadata`, `metric_definitions`, `sql_memories`, `query_runs`, `tool_calls`, `embedding_documents`
  - 已下载真实 Olist CSV，并导入 PostgreSQL
- 数据行数：
  - `users`: 99,441
  - `products`: 32,951
  - `orders`: 99,441
  - `order_items`: 112,650
  - `payments`: 103,886
  - `refunds`: 1,234
  - `reviews`: 98,410
  - `inventory_snapshots`: 32,951
  - `product_costs`: 32,951
  - `schema_metadata`: 78
  - `metric_definitions`: 4
- 验证：
  - `py -3 backend/scripts/init_db.py`
  - `py -3 backend/scripts/download_olist.py`
  - `py -3 backend/scripts/import_olist.py`
  - `py -3 backend/scripts/seed_metadata.py`
  - `py -3 backend/scripts/check_db.py`
  - `npm run backend:test`
  - `npm run test:e2e`
  - `npm run frontend:build`

### 4. 指标口径 PostgreSQL Repository

- commit: 本模块准备提交，提交信息为 `切换指标口径为PostgreSQL仓储并补全文档`
- 内容：
  - 补充 DataGrip 连接说明：`docs/database-datagrip.md`
  - 补充 PostgreSQL 数据基础模块完成文档
  - 将 `MetricRepository` 从内存仓储切换为 PostgreSQL `metric_definitions` 表
  - 更新指标 CRUD 测试，使用唯一测试指标名避免冲突
- 验证：
  - `npm run backend:test`
  - `npm run test:e2e`
  - `npm run frontend:build`

### 5. SQL Guard / Validator

- commit: 本模块准备提交，提交信息为 `实现SQL Guard和Validator并通过测试`
- 内容：
  - 新增 `SqlValidationRequest`, `SqlValidationResult`, `SqlGuardResult`
  - 新增 `validate_sql` 和 `guard_sql`
  - 使用 `sqlglot` 解析 PostgreSQL SQL
  - 覆盖只读、单语句、写操作拦截、白名单表、`SELECT *`、自动 LIMIT
- 验证：
  - `npm run backend:test`，12 个测试通过
  - `npm run test:e2e`
  - `npm run frontend:build`

### 6. 只读 SQL Executor

- commit: 本模块准备提交，提交信息为 `实现只读SQL Executor并通过测试`
- 内容：
  - 新增 `SqlExecutionResult`
  - 新增 `execute_guarded_sql`
  - Executor 只接受 Guard 放行后的 `final_sql`
  - 支持 `success`、`blocked`、`error` 三种结果状态
  - 执行结果转为 JSON-friendly 行数据
- 验证：
  - `npm run backend:test`，15 个测试通过
  - `npm run test:e2e`
  - `npm run frontend:build`

### 7. `/api/analyze` 真实 SQL 垂直切片

- commit: `ae9f129 接入analyze真实SQL工具链并通过测试`
- 内容：
  - 新增 `analysis_graph.py`，固定销售趋势问题先走真实 SQL 模板
  - 新增 `analysis_presenter.py`，将真实查询结果转为 `AnalyzeResponse`
  - `AgentService` 从 mock graph 切换到真实 Guard + Executor graph
  - `/api/analyze` 现在返回真实 PostgreSQL 查询结果
- 验证：
  - `npm run backend:test`，15 个测试通过
  - `npm run test:e2e`
  - `npm run frontend:build`

### 8. Schema + Metric Retriever 最小切片

- commit: `9956194 接入Schema和指标检索并通过测试`
- 内容：
  - 新增 `MetricContext`、`SchemaColumnContext`、`RetrievalContext`
  - 新增 `metric_retriever.py`，从 PostgreSQL `metric_definitions` 召回相关指标口径
  - 新增 `schema_retriever.py`，从 PostgreSQL `schema_metadata` 召回相关表字段
  - 新增 `context_builder.py`，组合指标和 schema 上下文
  - `/api/analyze` 在 SQL Guard / Executor 前先构建检索上下文
  - `AnalyzeResponse.source` 中的指标口径、表、字段改由召回上下文生成
- 验证：
  - `npm run backend:test`，18 个测试通过
  - `npm run test:e2e`
  - `npm run frontend:build`

### 9. Query Run Logging 运行记录

- commit: 本模块已提交并推送，提交信息为 `实现Query Run日志落库并通过测试`。
- 内容：
  - 新增 `QueryRunRecord`、`QueryRunDetail`、`ToolCallRecord`
  - 新增 `RunRepository`、`RunService` 和 `QueryRunLogger`
  - 新增开发者调试接口 `GET /api/runs`、`GET /api/runs/{run_id}`
  - `/api/analyze` 每次运行写入 `query_runs`
  - 关键工具调用写入 `tool_calls`：上下文召回、SQL Guard、SQL Executor、结果整理
  - README 已更新当前能力、API 入口和开发约定
- 验证：
  - `npm run backend:test`，20 个测试通过
  - `npm run test:e2e`
  - `npm run frontend:build`

## 当前架构边界

- React 只通过 `frontend/src/api/` 调 FastAPI。
- FastAPI API 层保持薄层。
- 业务逻辑放在 `services/`。
- Agent 编排放在 `agents/`。
- 确定性工具放在 `tools/`。
- 数据库访问后续放在 `db/repositories/`。
- 数据库结构必须放在 `backend/app/db/migrations/`。

## 当前正在做

Query Run Logging 运行记录模块已完成，已提交并推送。

## 下一步建议

按 `executable-plan-draft.md` 继续 M5/M7：

1. 开始 SQL Memory Retriever / Reuse Planner。
2. 增加 SQL Memory 写入条件和复用路径。
3. 后续再接 embedding / pgvector，让 schema/metric retriever 从关键词召回升级为混合检索。

## 已知风险

- 指标 CRUD 已接入 PostgreSQL，但测试仍直接使用本地库，后续需要独立测试库。
- `/api/analyze` 已接入真实 Guard + Executor 和 schema/metric retriever，但仍是固定 SQL 模板，尚未接入 LLM SQL Generator 和 SQL Memory。
- schema/metric retriever 当前是确定性关键词召回，尚未接入 embedding / pgvector 混合检索。
- `/api/runs` 是开发者调试接口，暂不放入普通用户主导航。
- `FastAPI TestClient` 当前有 `StarletteDeprecationWarning`，不影响功能，但后续可评估依赖版本。
- 用户最初提供的数据库用户名 `postgre` 认证失败；本机实际可用用户是 `postgres`。

## 每次继续开发前必须做

1. 读取本文件。
2. 读取相关 `docs/plans/*.md`。
3. 确认当前 git 状态。
4. 开发模块前创建或更新计划文档。
5. 模块完成后运行相关验证。
6. 更新本文件。
7. commit 并 push。
