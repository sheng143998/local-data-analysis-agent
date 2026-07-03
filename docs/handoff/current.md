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
- `/api/analyze` 已接入 SQL Memory 检索和成功写入，高置信历史成功问题可走 `fast_path` 复用 SQL。
- `/api/analyze` 已支持销售趋势 SQL 参数化模板，可解析“最近 N 天”并写入 `sql_memories.parameters`。
- `/api/analyze` 已接入 SQL Rewriter / Generator 最小切片，可识别“最近 90 天每月订单数是多少？”并生成月度订单数 SQL。
- `/api/analyze` 已接入 Top N 商品/品类销售额查询切片，可识别“销售额最高的前 10 个商品是什么？”和“哪个商品品类销售额最高？”。
- `/api/analyze` 已接入退款率 / 支付成功率查询切片，可识别“哪个商品品类退款率最高？”和“每个支付方式的成功率是多少？”。
- `/api/analyze` 已接入毛利率查询切片，可识别“最近 30 天毛利率最高的商品品类是什么？”。
- `/api/analyze` 已接入复购率 / 城市客单价查询切片，可识别“最近 90 天复购率是多少？”和“每个城市的客单价是多少？”。
- 已新增 Schema Metadata 自动同步能力，换库、导入新表或字段变化后可运行 `py -3 backend/scripts/sync_schema_metadata.py` 刷新 `schema_metadata`，避免继续堆固定 SQL 模板。
- 已新增统一 ModelAdapter 基础层，后续 SQL Generator / Rewriter 调用外部或本地 OpenAI-compatible 模型必须走 `backend/app/core/model_adapter.py`。
- 已新增 Model-backed SQL Generator 基础工具，可基于已召回 schema/metric 构造 prompt、调用 ModelAdapter、解析模型 JSON SQL；尚未接入 `/api/analyze` 主链路执行。
- `/api/analyze` 已通过 `MODEL_SQL_GENERATOR_ENABLED` 配置开关接入 Model SQL Generator 的 `cold_path` 尝试路径；默认关闭，开启后模型 SQL 仍必经 Guard / Executor，失败会回退确定性生成。
- 已新增标准问题评估集基础设施，`npm run eval:standard` 可运行 20 个 V1 标准问题并生成 `eval/reports/latest_eval_report.json`。
- 标准问题评估已增强断言指标，报告区分 `execution_success_rate` 和 `strict_success_rate`，并输出表/关键词断言失败案例。
- SQL Memory `fast_path` 已增加关键表约束，用户、流量、优惠券等问题缺少关键表时不再直接复用历史 SQL。

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

- commit: 本模块已提交并推送，提交信息为 `切换指标口径为PostgreSQL仓储并补全文档`。
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

- commit: 本模块已提交并推送，提交信息为 `实现SQL Guard和Validator并通过测试`。
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

- commit: 本模块已提交并推送，提交信息为 `实现只读SQL Executor并通过测试`。
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

### 10. SQL Memory Retriever / Reuse Planner 最小切片

- commit: 本模块已提交并推送，提交信息为 `实现SQL Memory检索复用并通过测试`。
- 内容：
  - 新增 `SqlMemoryRecord`、`SqlMemoryCandidate`、`SqlReusePlan`、`SqlMemoryUpsert`
  - 新增 `SqlMemoryRepository`、`MemoryService` 和 `/api/memories` 调试接口
  - 新增 `retrieve_sql_memory`、`plan_sql_reuse`、`upsert_successful_sql_memory`
  - `/api/analyze` 会先检索 SQL Memory，再决定 `fast_path` 或 `cold_path`
  - 查询成功后写入或更新 `sql_memories`
  - `query_runs.memory_hit` 会记录是否命中历史 SQL
- 验证：
  - `npm run backend:test`，24 个测试通过
  - `npm run test:e2e`
  - `npm run frontend:build`

### 11. SQL Memory 参数化模板与时间范围改写

- commit: 本模块已提交并推送，提交信息为 `实现SQL Memory参数化模板并通过测试`。
- 内容：
  - 新增 `SalesTrendParameters`
  - 新增 `parse_sales_trend_parameters` 和 `render_sales_trend_sql`
  - `/api/analyze` 会从用户问题解析“最近 N 天”并渲染销售趋势 SQL
  - 高置信 SQL Memory 命中时会按当前问题重新渲染 SQL
  - `sql_memories.parameters` 写入 `days` 和 `granularity`
- 验证：
  - `npm run backend:test`，28 个测试通过
  - `npm run test:e2e`
  - `npm run frontend:build`

### 12. SQL Rewriter / Generator 最小切片

- commit: `2ca2874 实现SQL Rewriter最小切片并通过测试`
- 内容：
  - 新增 `GeneratedSql`
  - 新增 `generate_or_rewrite_sales_sql`
  - 扩展 `SalesTrendParameters`，支持 `granularity` 和 `metric`
  - 支持“最近 90 天每月订单数是多少？”生成月度订单数 SQL
  - `/api/analyze` 在 SQL Memory 规划后、Guard 前执行 SQL 生成/改写节点
  - `tool_calls` 新增 SQL 生成/改写工具调用记录
- 验证：
  - `npm run backend:test`，33 个测试通过
  - `npm run test:e2e`
  - `npm run frontend:build`

### 13. Top N 商品/品类销售额查询切片

- commit: 本模块已提交并推送，提交信息为 `实现TopN商品品类查询并通过测试`。
- 内容：
  - 扩展 `SalesTrendParameters.metric`，支持 `top_product_sales` 和 `top_category_sales`
  - 新增 `limit` 参数解析，支持“前 10 个商品”等 Top N 问法
  - 商品/品类问题自动召回 `order_items`、`products`、`payments` 相关 schema
  - `/api/analyze` 可执行商品销售额 Top N 和品类销售额排行真实 SQL
  - 聊天页结果表头调整为更通用的“维度 / 销售额”
- 验证：
  - `npm run backend:test`，38 个测试通过
  - `npm run test:e2e`
  - `npm run frontend:build`

### 14. 退款率 / 支付成功率查询切片

- commit: `ec677d3 实现退款率支付成功率查询并通过测试`
- 内容：
  - 扩展 `SalesTrendParameters.metric`，支持 `category_refund_rate`、`payment_success_rate`、`payment_failure_rate`
  - 支持“哪个商品品类退款率最高？”生成品类退款率 SQL
  - 支持“每个支付方式的成功率是多少？”生成支付方式成功率 SQL
  - 退款类问题自动召回 `refunds`、`order_items`、`products`、`payments` 相关 schema
  - Presenter 兼容 `refund_rate`、`success_rate`、`failure_rate` 结果列
- 验证：
  - `npm run backend:test`，43 个测试通过
  - `npm run test:e2e`
  - `npm run frontend:build`

### 15. 毛利率查询切片

- commit: `98322e7 实现毛利率查询并通过测试`
- 内容：
  - 扩展 `SalesTrendParameters.metric`，支持 `category_gross_margin`
  - 支持“最近 30 天毛利率最高的商品品类是什么？”生成品类毛利率 SQL
  - 毛利率问题自动召回 `order_items`、`products`、`product_costs`、`payments` 相关 schema
  - Presenter 兼容 `gross_margin` 结果列
- 验证：
  - `npm run backend:test`，46 个测试通过
  - `npm run test:e2e`
  - `npm run frontend:build`

### 16. 复购率 / 城市客单价查询切片

- commit: `d98f88c 实现复购率城市客单价查询并通过测试`
- 内容：
  - 扩展 `SalesTrendParameters.metric`，支持 `repeat_purchase_rate`、`city_avg_order_value`
  - 支持“最近 90 天复购率是多少？”生成整体复购率 SQL
  - 支持“每个城市的客单价是多少？”生成城市客单价 SQL
  - 用户维度问题自动召回 `users`、`orders`、`payments`、`refunds` 相关 schema
  - Presenter 兼容 `segment_label`、`city_label`、`repeat_rate` 结果列
- 验证：
  - `npm run backend:test`，51 个测试通过
  - `npm run test:e2e`
  - `npm run frontend:build`

### 17. Schema Metadata 自动同步

- commit: `ec5c0e1 实现Schema元数据自动同步并通过测试`
- 内容：
  - 新增 `SchemaSyncService`，从 PostgreSQL `information_schema.columns` 同步当前 `public` schema 的真实表字段
  - 新增 `backend/scripts/sync_schema_metadata.py`，用于换库、导入新表或字段变化后的手动刷新
  - 新增 `004_schema_metadata_unique.sql`，清理重复元数据并创建 `(table_name, column_name)` 唯一索引
  - `seed_metadata.py` 改为复用同步服务，减少重复 schema 写入逻辑
  - 新增 `test_schema_sync_service.py`，覆盖过滤、字段读取和 upsert 保留人工说明逻辑
- 验证：
  - `npm run backend:test`，54 个测试通过
  - `py -3 backend/scripts/init_db.py`
  - `py -3 backend/scripts/sync_schema_metadata.py`，同步 12 张表、78 个字段
  - `npm run test:e2e`
  - `npm run frontend:build`

### 18. 统一 ModelAdapter 基础层

- commit: `25ac0dc 实现统一ModelAdapter基础层并通过测试`
- 内容：
  - 扩展 `backend/app/core/config.py`，支持模型 provider、base URL、model、API key、timeout、retry 配置
  - 新增 `backend/app/core/model_adapter.py`，提供 OpenAI-compatible chat completions 统一入口
  - 支持结构化 `ModelRequest`、`ModelResponse`、`ModelUsage`，并把空消息、HTTP 错误、transport 异常转换为结构化错误
  - 支持可注入 transport，测试不依赖真实模型服务或真实 API key
  - 更新 `backend/.env.example`，只保留模型配置占位值
- 验证：
  - `npm run backend:test`，59 个测试通过

### 19. Model-backed SQL Generator 基础工具

- commit: `75a6627 实现模型SQL生成基础工具并通过测试`
- 内容：
  - 新增 `backend/app/tools/model_sql_generator.py`
  - 基于 `RetrievalContext` 和 `SqlReusePlan` 构造受控 prompt，只使用召回到的表字段和指标口径
  - 通过 `ModelAdapter.chat()` 调用 OpenAI-compatible 模型，要求 JSON response format
  - 解析模型响应为 `GeneratedSql`，新增 `model_generate`、`model_rewrite`、`model_error` 路径
  - 模型生成 SQL 当前不直接执行，后续接主链路时仍必须经过 Validator / Guard / Executor
  - 新增 `test_model_sql_generator.py`，覆盖 prompt、JSON 解析、warning、成功生成和模型错误路径
- 验证：
  - `npm run backend:test`，64 个测试通过

### 20. Model SQL Generator cold_path 配置开关接入

- commit: `5ab8b4f 接入模型SQL生成cold_path并通过测试`
- 内容：
  - 新增 `MODEL_SQL_GENERATOR_ENABLED` 配置，默认关闭模型 SQL 生成
  - `analysis_graph._select_generated_sql()` 负责集中选择 SQL 生成路径
  - 开启配置且 `reuse_plan.path_type == "cold_path"` 时调用 `generate_sql_with_model()`
  - 模型返回 SQL 后继续进入现有 SQL Guard 和只读 Executor
  - 模型失败或未返回 SQL 时回退 `generate_or_rewrite_sales_sql()`
  - 新增 `test_analysis_graph_sql_selection.py` 覆盖关闭、开启、回退和 rewrite_path 不调用模型
- 验证：
  - `npm run backend:test`，68 个测试通过

### 21. 标准问题评估集基础设施

- commit: `e8df5ae 建立标准问题评估集并通过测试`
- 内容：
  - 新增 `eval/datasets/standard_questions.jsonl`，包含 20 个 V1 标准问题
  - 新增 `eval/scripts/run_eval.py`，可逐条调用 `/api/analyze` 并生成评估报告
  - 新增 `eval/reports/latest_eval_report.json`，记录最近一次评估结果
  - 新增 `npm run eval:standard`
  - 新增 `test_eval_runner.py`，覆盖数据集读取和报告指标汇总
  - README 增加标准问题评估说明
- 验证：
  - `npm run backend:test`，70 个测试通过
  - `npm run eval:standard`，20/20 链路执行成功

### 22. 标准问题评估断言增强

- commit: `375de27 增强标准问题评估断言并通过测试`
- 内容：
  - `EvalCaseResult` 新增 `missing_tables`、`missing_keywords`、`table_match`、`keyword_match`、`strict_ok`
  - 评估报告新增 `strict_success_count`、`strict_success_rate`、`table_match_rate`、`keyword_match_rate`、`assertion_failures`
  - CLI 输出新增严格成功率
  - 测试覆盖“链路成功但断言失败”的情况
  - README 增加评估指标解释
- 验证：
  - `npm run backend:test`，71 个测试通过
  - `npm run eval:standard`，20/20 链路执行成功，严格成功率 55%

### 23. SQL Memory fast_path 表/意图约束

- commit: `6a12c25 增强SQLMemory复用约束并通过测试`
- 内容：
  - `SqlMemoryCandidate` 新增 `required_table_match` 和 `required_tables`
  - `retrieve_sql_memory()` 根据问题推断用户、流量、优惠券等关键表，并检查候选 SQL 是否包含这些表
  - `plan_sql_reuse()` 要求高分且关键表匹配才允许 `fast_path`
  - 缺少关键表的高分候选降级为 `rewrite_path`
  - 新增单元测试覆盖阻止错误 fast_path 和允许合法 fast_path
- 验证：
  - `npm run backend:test`，73 个测试通过
  - `npm run eval:standard`，20/20 链路执行成功，严格成功率 55%，memory hit 从 100% 降到 60%

### 24. V1 核心文档补齐

- commit: `39ac317 补齐V1核心文档并通过验证`
- 内容：
  - 新增 `docs/architecture.md`，说明 V1 架构、产品边界和主链路。
  - 新增 `docs/data_model.md`，说明业务表、Agent 元数据表、迁移和指标口径。
  - 新增 `docs/agent_workflow.md`，说明 `/api/analyze` 的检索、记忆、SQL 选择、Guard、Executor、日志和记忆写入链路。
  - 新增 `docs/sql_guard.md`，说明 Validator、Guard、白名单表和只读 Executor。
  - 新增 `docs/sql_memory.md`，说明 SQL Memory 打分、fast_path 关键表约束和写入条件。
  - 新增 `docs/evaluation.md`，说明标准问题评估集、报告字段和当前基线。
  - README 增加 V1 核心文档入口。
- 验证：
  - `npm run backend:test`，73 个测试通过
  - `npm run eval:standard`，20/20 链路执行成功，严格成功率 55%
  - `npm run test:e2e`
  - `npm run frontend:build`

### 25. V1 接口文档补齐

- commit: `2f62bc0 补齐V1中文接口文档并通过验证`
- 内容：
  - 新增 `docs/api.md`，按普通业务接口和开发者调试接口分层说明当前 API。
  - 覆盖 `GET /api/health`、`POST /api/analyze`、指标口径 CRUD、运行记录和 SQL Memory 调试接口。
  - 中文说明请求参数、响应字段、错误边界、接口用途和当前风险。
  - README 增加 `docs/api.md` 入口，并在 API 入口段落链接完整接口文档。
  - 本模块只更新文档，不修改后端接口、前端页面、数据库结构或 Agent 行为。
- 验证：
  - `npm run backend:test`，73 个测试通过
  - `npm run test:e2e`
  - `npm run frontend:build`

### 26. 前后端接口映射文档

- commit: 本模块已验证，随本次提交推送完成，提交信息为 `补齐前后端接口映射文档并通过验证`。
- 内容：
  - 新增 `docs/api_frontend_mapping.md`，说明前端 API client、TypeScript 类型和后端接口的映射关系。
  - 记录 `analysisClient.ts`、`metricClient.ts` 当前调用的后端路径和页面入口。
  - 明确后端 `AnalyzeResponse.trace`、`AnalyzeResponse.steps` 当前未进入前端类型和普通用户页面。
  - README 和 `docs/api.md` 增加映射文档入口。
  - 本模块只更新中文文档，不修改前端、后端、数据库或 Agent 行为。
- 验证：
  - `npm run frontend:build`
  - `npm run backend:test`，73 个测试通过
  - `npm run test:e2e`

## 当前架构边界

- React 只通过 `frontend/src/api/` 调 FastAPI。
- FastAPI API 层保持薄层。
- 业务逻辑放在 `services/`。
- Agent 编排放在 `agents/`。
- 确定性工具放在 `tools/`。
- 数据库访问后续放在 `db/repositories/`。
- 数据库结构必须放在 `backend/app/db/migrations/`。

## 当前正在做

前后端接口映射文档已补齐且验证通过，准备随本次提交推送完成。本轮只做接口文档和 README 等中文文档，不修改功能代码。

## 下一步建议

按用户最新目标继续推进 V1 文档类任务，优先补齐接口相关中文说明：

1. 如接口字段继续变化，优先同步 `docs/api.md`、README 和对应模块说明。
2. 后续可补充错误码、权限边界和上线前鉴权说明。
3. 后续如果建设开发者调试页，再补 `/api/runs`、`/api/memories` 的前端映射说明。

## 已知风险

- 指标 CRUD 已接入 PostgreSQL，但测试仍直接使用本地库，后续需要独立测试库。
- `/api/analyze` 已接入真实 Guard + Executor、schema/metric retriever、SQL Memory 和确定性 SQL Rewriter / Generator，但仍未接入真实 LLM SQL Generator / Rewriter。
- ModelAdapter 基础层已完成，但 `/api/analyze` 尚未使用真实模型生成 SQL。
- Model SQL Generator 已接入 analysis graph 的 `cold_path` 尝试路径，但默认关闭，尚未用真实模型服务跑标准问题评估集。
- 标准问题评估已可运行并区分严格断言；最近一次 20/20 链路成功，严格成功率 55%。SQL Memory fast_path 已更保守，但部分语义仍需模型生成或更强意图生成修复。
- schema/metric retriever 当前是确定性关键词召回，尚未接入 embedding / pgvector 混合检索。
- SQL Memory 当前 semantic similarity 暂用文本相似度替代，尚未接入 embedding / pgvector。
- Schema Metadata 已支持自动同步字段结构，但尚未自动生成 embedding 或完整业务含义。
- 销售趋势“最近 N 天”当前用最近 N 个有交易日期表达，不是严格自然日窗口；Top N 和复杂指标查询当前暂不带时间窗口。
- 支付成功率当前基于 `payments.status = 'paid'`，真实失败状态样本仍需后续数据增强。
- 毛利率当前基于合成 `product_costs.unit_cost`，后续可替换为真实成本口径。
- 复购率当前暂按全量已支付用户订单计算，未严格套用“最近 90 天”自然日窗口。
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

