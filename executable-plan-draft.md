# 本地数据分析 Agent V1 可执行研发方案

## 0. 当前项目事实

本项目已经完成第一轮产品和工程骨架调整，当前事实如下：

- 前端目录：`frontend/`
- 后端目录：`backend/`
- 前端技术栈：React + Vite + TypeScript + Tailwind CSS + React Query + ECharts + TanStack Table
- 后端技术栈：FastAPI + Pydantic
- 当前最小闭环：前端聊天页 -> `POST /api/analyze` -> FastAPI -> `AgentService` -> mock Agent graph -> 返回 SQL、自然语言分析、结果表和来源信息
- 当前普通用户界面：聊天式数据问答、数据源、指标口径 CRUD、个人中心、系统设置
- 当前不在普通用户界面展示：SQL 记忆详情、评估报告、模型名称、数据库连接状态、向量模型、prompt、工具调用原始日志

V1 后续研发必须在这个事实基础上推进，不再回到 SQLite、Streamlit 或单页 dashboard 路线。

## 1. V1 产品定位

V1 目标是做一个面向业务分析人员的本地化 AI 数据分析 Agent。用户不需要懂 SQL，也不需要理解模型、向量库或数据库连接状态，只需要像聊天一样提出业务问题。

系统负责：

1. 理解用户问题。
2. 检索指标口径、数据表结构和历史成功 SQL。
3. 选择 `fast_path`、`rewrite_path` 或 `cold_path`。
4. 生成、复用或改写 SQL。
5. 通过 SQL Validator 和 SQL Guard。
6. 使用只读连接执行 PostgreSQL 查询。
7. 返回自然语言结论、最终 SQL、来源信息、结果表和简单图表。
8. 成功查询写入 SQL Memory。
9. 查询过程写入 `query_runs` 和 `tool_calls`，供开发者调试和评估。

普通用户看到的是“可信分析结果”。开发者看到的是“可追踪 Agent 执行链路”。

## 2. V1 明确不做

V1 不做以下内容：

- 不做完整通用 BI 拖拽式报表。
- 不做多租户复杂权限系统。
- 不做生产级 vLLM 部署。
- 不把 QLoRA 微调作为第一阶段主线。
- 不让 LLM 直接执行 SQL。
- 不在普通用户界面展示 prompt、原始模型输出、SQL 记忆相似度、工具调用 payload。

这些能力可以进入 V2 或开发者页面，但不能阻塞 V1 主链路。

## 3. 推荐项目目录

当前目录已经按前后端拆分，后续应逐步补齐以下结构：

```text
local-data-analysis-agent/
  frontend/
    src/
      api/
        analysisClient.ts
        metricClient.ts
        dataSourceClient.ts
      types/
        analysis.ts
        metric.ts
        dataSource.ts
      components/
      pages/
    dist/
    package.json

  backend/
    app/
      main.py
      api/
        routes.py
        analysis.py
        metrics.py
        data_sources.py
        runs.py
        memories.py
      schemas/
        analysis.py
        metrics.py
        data_sources.py
        runs.py
        memories.py
      services/
        agent_service.py
        metric_service.py
        data_source_service.py
        run_service.py
        memory_service.py
      agents/
        graph.py
        state.py
        nodes.py
        routing.py
      tools/
        schema_tools.py
        metric_tools.py
        memory_tools.py
        sql_generation_tools.py
        sql_validation_tools.py
        sql_execution_tools.py
        presentation_tools.py
      db/
        connection.py
        repositories/
        migrations/
          001_extensions.sql
          002_business_tables.sql
          003_agent_metadata.sql
          004_indexes.sql
      core/
        config.py
        logging.py
        errors.py
        model_adapter.py
    tests/
    requirements.txt

  docs/
    plans/
    architecture.md
    data_model.md
    agent_workflow.md
    sql_memory.md
    sql_guard.md
    evaluation.md

  eval/
    datasets/
      standard_questions.jsonl
    scripts/
      run_eval.py
    reports/
```

## 4. 前端产品形态

### 4.1 普通用户页面

普通用户只需要以下页面：

- 数据问答：ChatGPT 风格会话页，左侧会话历史，中间对话流。
- 数据源：展示业务数据集、表说明、字段说明，但不展示数据库连接串。
- 指标口径：业务指标 CRUD，支持新增、编辑、删除、搜索、查看详情。
- 个人中心：账号与使用统计。
- 系统设置：面向业务配置，默认不展示模型、向量库、数据库连接细节。

### 4.2 数据问答页输出

一次回答至少包含：

- 自然语言分析结论。
- 最终执行 SQL。
- 简单结果表。
- 数据来源：数据集、表、字段、指标口径。
- 可信说明：只读查询、执行成功、返回行数、查询耗时、数据时间范围。

回答应像业务分析师报告，而不是开发者调试面板。

### 4.3 开发者信息放置原则

以下内容不在普通用户页面默认展示：

- SQL Memory 命中候选。
- `fast_path` / `rewrite_path` / `cold_path` 内部评分。
- LangGraph node 原始 state。
- prompt。
- 模型原始输出。
- 工具调用 input/output payload。

这些内容进入：

- 后端日志。
- `/api/runs`。
- `/api/memories`。
- 后续开发者调试页。

## 5. 后端 API 契约

### 5.1 `GET /api/health`

用于服务健康检查。

Response:

```json
{
  "ok": true,
  "service": "local-data-analysis-agent",
  "version": "0.1.0"
}
```

### 5.2 `POST /api/analyze`

用于聊天式数据问答。

Request:

```json
{
  "question": "最近 30 天销售额按天变化如何？",
  "session_id": "optional-session-id"
}
```

Response:

```json
{
  "question": "最近 30 天销售额按天变化如何？",
  "path": "rewrite_path",
  "summary": "最近 30 天销售额整体呈稳步上升趋势...",
  "sql": "SELECT ...",
  "metrics": [],
  "rows": [],
  "source": {
    "dataset": "Olist 巴西电商公开数据集 + 合成增强数据",
    "tables": ["orders", "payments"],
    "fields": ["created_at", "status", "total_amount"],
    "metricDefinition": "销售额 = 已支付订单 total_amount 汇总",
    "range": "2026-06-03 至 2026-07-03",
    "returnedRows": 1240,
    "queryTime": "120ms",
    "security": "只读 SELECT"
  },
  "trace": {
    "toolCalls": 6,
    "modelCalls": 1,
    "memoryCandidates": 3,
    "totalTime": "912ms"
  },
  "steps": []
}
```

### 5.3 指标 CRUD API

指标口径是业务资产，必须支持 CRUD。

建议接口：

- `GET /api/metrics`
- `GET /api/metrics/{metric_id}`
- `POST /api/metrics`
- `PUT /api/metrics/{metric_id}`
- `DELETE /api/metrics/{metric_id}`

Metric 字段：

```json
{
  "id": "uuid",
  "metric_name": "sales_amount",
  "display_name": "销售额",
  "description": "已支付订单 total_amount 汇总",
  "formula": "SUM(orders.total_amount)",
  "required_tables": ["orders", "payments"],
  "required_fields": ["orders.total_amount", "payments.status"],
  "default_filters": {
    "payments.status": "paid"
  },
  "example_question": "最近 7 天销售额是多少？",
  "owner": "经营分析组",
  "status": "enabled",
  "created_at": "2026-07-03T00:00:00",
  "updated_at": "2026-07-03T00:00:00"
}
```

### 5.4 开发者调试 API

后续补充：

- `GET /api/runs`
- `GET /api/runs/{run_id}`
- `GET /api/memories`
- `GET /api/memories/{memory_id}`

这些 API 不出现在普通用户主导航。

## 6. 数据库设计

V1 使用 PostgreSQL。业务数据存关系表，向量只用于 schema、指标、SQL 记忆和文档检索。

### 6.1 必需扩展

```sql
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS pg_trgm;
```

### 6.2 业务表

核心交易表：

- `users`
- `products`
- `orders`
- `order_items`
- `payments`
- `refunds`

分析增强表：

- `traffic_events`
- `coupons`
- `coupon_usages`
- `reviews`
- `inventory_snapshots`
- `product_costs`

### 6.3 Agent 元数据表

`schema_metadata`：

- 表字段说明，用于 schema 检索。
- 包含 `embedding vector(1536)`。

`metric_definitions`：

- 业务指标口径。
- 支持 CRUD。
- 包含 `embedding vector(1536)`。

`sql_memories`：

- 历史成功 SQL、问题模板、参数 schema、指标、维度、成功率。
- 包含 `question_embedding vector(1536)` 和 `sql_embedding vector(1536)`。

`query_runs`：

- 每次用户查询运行记录。
- 记录路径、SQL、执行状态、错误、行数、耗时。

`tool_calls`：

- 每次工具调用记录。
- 记录工具名、输入摘要、输出摘要、状态、耗时、错误。

`embedding_documents`：

- 通用 RAG 文档。
- 存放 schema 文档、指标文档、业务规则、示例问答。

### 6.4 索引策略

V1 默认使用 HNSW：

```sql
CREATE INDEX idx_schema_metadata_embedding
ON schema_metadata
USING hnsw (embedding vector_cosine_ops);

CREATE INDEX idx_metric_definitions_embedding
ON metric_definitions
USING hnsw (embedding vector_cosine_ops);

CREATE INDEX idx_sql_memories_question_embedding
ON sql_memories
USING hnsw (question_embedding vector_cosine_ops);

CREATE INDEX idx_sql_memories_sql_embedding
ON sql_memories
USING hnsw (sql_embedding vector_cosine_ops);
```

文本相似度索引：

```sql
CREATE INDEX idx_sql_memories_question_trgm
ON sql_memories
USING gin (normalized_question gin_trgm_ops);
```

## 7. LangGraph 工作流

V1 使用 LangGraph `StateGraph`。每个节点必须可追踪、可测试、可记录。

```text
Query Context Builder
-> SQL Memory Retriever
-> Schema Retriever
-> Metric Retriever
-> SQL Reuse Planner
-> SQL Template Renderer / SQL Rewriter / SQL Generator
-> SQL Validator
-> SQL Guard
-> SQL Executor
-> Result Presenter
-> Query Run Logger
-> SQL Memory Updater
```

### 7.1 路径选择

`fast_path`：

- SQL Memory 高置信命中。
- 问题只改变时间范围、品类、城市、Top N 等参数。
- 不调用 SQL Generator。
- 仍经过 Validator、Guard、Executor。

`rewrite_path`：

- SQL Memory 中置信命中。
- 需要增加维度、过滤条件或改写聚合方式。
- 使用历史 SQL + schema + 指标口径调用 SQL Rewriter。

`cold_path`：

- 没有可用 SQL Memory。
- 完整执行 schema 检索、指标检索和 SQL 生成。

### 7.2 State 字段

最小 state：

- `question`
- `session_id`
- `chat_history`
- `memory_candidates`
- `memory_hit`
- `path_type`
- `reuse_type`
- `schema_context`
- `metric_context`
- `generated_sql`
- `validated_sql`
- `final_sql`
- `validation_errors`
- `guard_errors`
- `execution_result`
- `answer`
- `chart_spec`
- `sources`
- `steps`
- `trace`
- `latency_ms`
- `error`

### 7.3 节点职责

`SQL Memory Retriever`：

- 混合检索 SQL 记忆。
- 返回候选、相似度、历史成功率、可复用模板。

`Schema Retriever`：

- 根据问题和记忆候选召回表字段。
- 不允许 SQL Generator 使用未召回或未白名单表。

`Metric Retriever`：

- 召回指标口径。
- 销售额、退款率、复购率等必须按指标定义生成 SQL。

`SQL Reuse Planner`：

- 决定 `fast_path`、`rewrite_path`、`cold_path`。
- 输出 `reuse_type`、参数、是否需要模型。

`SQL Validator`：

- 使用 `sqlglot` 做语法和结构校验。
- 检查 PostgreSQL 方言、表字段存在、白名单、`SELECT *`、缺失 LIMIT、明显大表扫描。

`SQL Guard`：

- 只允许 SELECT。
- 禁止多语句。
- 禁止 DDL/DML。
- 禁止访问非白名单表。
- 自动注入或修正 LIMIT。

`SQL Executor`：

- 使用只读数据库账号。
- 设置 statement timeout。
- 返回列名、行数据、行数、耗时。

`Result Presenter`：

- 生成中文业务结论。
- 组织图表建议和前端展示结构。

## 8. 工具函数清单

V1 工具先做确定性 Python 函数，不让 LLM 直接调用数据库。

- `retrieve_sql_memory(input) -> SqlMemoryResult`
- `retrieve_schema(input) -> SchemaContext`
- `retrieve_metrics(input) -> MetricContext`
- `plan_sql_reuse(input) -> ReusePlan`
- `render_sql_template(input) -> RenderedSql`
- `generate_sql(input) -> GeneratedSql`
- `rewrite_sql(input) -> GeneratedSql`
- `validate_sql(input) -> ValidationResult`
- `guard_sql(input) -> GuardResult`
- `execute_sql(input) -> ExecutionResult`
- `present_result(input) -> PresentedAnswer`
- `log_tool_call(input) -> ToolCallRecord`
- `update_sql_memory(input) -> MemoryUpdateResult`

每个工具要求：

- Pydantic 输入输出。
- 记录工具调用。
- 结构化错误。
- 单元测试覆盖正常和失败路径。

## 9. 模型适配器

外部模型调用必须走统一 adapter，不允许在节点里直接调用 SDK。

`ModelAdapter` 需要支持：

- OpenAI-compatible chat completions。
- timeout。
- retry。
- structured error。
- latency。
- token metadata。
- provider/model 字段进入 trace，但默认不展示给普通用户。

V1 可先支持一个 provider，接口要为后续 Ollama、llama.cpp server、DashScope、OpenAI-compatible API 留好。

Embedding adapter 也必须统一：

- 模型：`text-embedding-v4`
- 维度：1536
- 输出：dense vector
- 用途：schema、metrics、SQL memories、documents

## 10. SQL Memory 机制

### 10.1 写入条件

只有满足以下条件才写入 SQL Memory：

- SQL Guard 通过。
- SQL 执行成功。
- 使用白名单表。
- 查询结果结构合理。
- 没有访问敏感字段。
- 用户问题和 SQL 可形成可复用模板。

### 10.2 复用类型

- `direct_reuse`
- `parameter_rewrite`
- `dimension_extend`
- `filter_extend`
- `subquery_reuse`
- `regenerate`

### 10.3 混合检索打分

建议：

```text
score = 0.45 * semantic_similarity
      + 0.25 * text_similarity
      + 0.20 * metric_table_match
      + 0.10 * success_score
```

阈值：

- `score >= 0.88`：`fast_path`
- `0.70 <= score < 0.88`：`rewrite_path`
- `score < 0.70`：`cold_path`

## 11. 开发里程碑

### M0：当前最小闭环整理

已完成：

- `frontend/` 与 `backend/` 拆分。
- FastAPI mock API。
- 聊天式前端。
- 指标口径前端 CRUD。
- 前端构建与后端 smoke 测试。

退出条件：

- `npm run frontend:build` 通过。
- `npm run backend:test` 通过。
- `npm run test:e2e` 通过。

### M1：数据库与迁移

交付：

- PostgreSQL Docker Compose 或本地连接说明。
- `db/migrations/001_extensions.sql`
- `002_business_tables.sql`
- `003_agent_metadata.sql`
- `004_indexes.sql`
- seed 脚本。
- Olist + 合成增强数据导入脚本。

退出条件：

- 一条命令初始化数据库。
- 12 张业务表可用。
- Agent 元数据表可用。
- pgvector 和 pg_trgm 可用。

### M2：指标口径后端 CRUD

交付：

- `GET/POST/PUT/DELETE /api/metrics`
- `metric_definitions` repository。
- 前端指标 CRUD 从本地 state 改为 API 持久化。
- 指标 embedding 写入占位或真实 adapter。

退出条件：

- 新增、编辑、删除指标会持久化。
- 数据问答能读取指标口径。
- API 测试覆盖 CRUD。

### M3：SQL Guard + Validator

交付：

- `sqlglot` validator。
- Guard 只允许 SELECT。
- 自动 LIMIT。
- 白名单表校验。
- 单元测试覆盖危险 SQL。

退出条件：

- `DROP/DELETE/UPDATE/INSERT/ALTER` 被拦截。
- 多语句被拦截。
- 非白名单表被拦截。
- 安全 SELECT 能通过。

### M4：只读 SQL Executor

交付：

- PostgreSQL 只读连接。
- statement timeout。
- row limit。
- 执行结果标准化。

退出条件：

- 能执行标准问题 SQL。
- 错误能结构化返回。
- 不允许写操作绕过 Guard。

### M5：Schema + Metric Retriever

交付：

- schema metadata 读取。
- 指标口径召回。
- 关键词检索先行，embedding 检索后补。

退出条件：

- 标准问题能召回相关表字段和指标。
- SQL Generator 不依赖全量 schema prompt。

### M6：SQL Generator / Rewriter

交付：

- 统一 ModelAdapter。
- SQL Generator。
- SQL Rewriter。
- prompt 模板。
- 基础修复逻辑。

退出条件：

- 20 个标准问题至少 12 个端到端成功。
- 生成 SQL 必经 Validator 和 Guard。

### M7：SQL Memory

交付：

- SQL Memory 写入。
- 混合检索。
- Reuse Planner。
- Template Renderer。
- `/api/memories` 调试接口。

退出条件：

- 参数变化问题走 `fast_path`。
- 相似改写问题走 `rewrite_path`。
- `/api/runs` 可看到路径和记忆命中。

### M8：评估

交付：

- 20-30 个标准问题。
- 自动评估脚本。
- 报告字段：执行成功率、SQL 生成成功率、记忆命中率、复用成功率、平均延迟、路径占比、失败案例。

退出条件：

- 每次核心改动后能跑评估。
- 失败案例可追踪到 run 和 tool call。

## 12. 标准问题集

基础查询：

1. 最近 7 天销售额是多少？
2. 最近 30 天每天的销售额是多少？
3. 最近 90 天每月订单数是多少？
4. 销售额最高的前 10 个商品是什么？
5. 哪个商品品类销售额最高？

复杂指标：

6. 最近 30 天支付失败率是多少？
7. 哪个商品品类退款率最高？
8. 最近 180 天每月退款率是多少？
9. 最近 30 天毛利率最高的商品品类是什么？
10. 每个支付方式的成功率是多少？

用户分析：

11. 过去 6 个月每月新增用户数是多少？
12. 最近 30 天下单用户数是多少？
13. 购买次数最多的前 10 个用户是谁？
14. 最近 90 天复购率是多少？
15. 每个城市的客单价是多少？

漏斗与营销：

16. 最近 30 天访问到下单转化率是多少？
17. 最近 30 天加购到支付转化率是多少？
18. 哪些优惠券核销率最高？
19. 使用优惠券的订单客单价是否更高？
20. 流量来源带来的订单转化率是多少？

SQL 记忆与追问：

21. 最近 7 天销售额是多少？
22. 那最近 30 天呢？
23. 按天拆开看。
24. 只看服饰品类。
25. 这些订单的退款率是多少？

## 13. 验收标准

V1 完成时必须满足：

- 普通用户能通过聊天页完成一次真实 PostgreSQL 查询。
- 前端展示自然语言结论、SQL、表格、图表、来源和可信说明。
- SQL 必经 Validator 和 Guard。
- 后端记录 `query_runs` 和 `tool_calls`。
- 指标口径支持 API CRUD 和前端 CRUD。
- 高频相似问题能复用 SQL Memory。
- 至少 20 个标准问题评估集可运行。
- 文档能说明架构、数据模型、Agent 工作流、SQL Guard、SQL Memory 和评估方式。

## 14. 下一步执行顺序

建议下一步从 M1 和 M2 开始：

1. 创建 PostgreSQL migration 目录与 extensions/business/metadata 表结构。
2. 实现 `metric_definitions` 后端 CRUD。
3. 将前端指标 CRUD 从本地 state 接到 `/api/metrics`。
4. 添加 API 测试。
5. 再进入 SQL Guard 和只读 Executor。

这个顺序的好处是：先把业务口径和数据库基础打牢，再接模型和 LangGraph，风险更低。
