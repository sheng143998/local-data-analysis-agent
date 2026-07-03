# 模块：Schema + Metric Retriever 最小切片

当前状态：模块已完成，已通过 `npm run backend:test`、`npm run test:e2e` 和 `npm run frontend:build` 验证；当前等待提交并推送。

业务逻辑：当业务分析人员在数据问答中提出“最近 30 天销售额按天变化如何？”这类问题时，后端会先从 PostgreSQL 的 `metric_definitions` 召回相关指标口径，再从 `schema_metadata` 召回相关表字段。分析结果仍返回用户友好的自然语言结论、SQL、表格和来源说明，但 `source.metricDefinition`、`source.tables` 和 `source.fields` 已由数据库元数据生成，不再只靠 presenter 内部硬编码。

关键代码：

- `backend/app/schemas/retrieval.py`：定义 `MetricContext`、`SchemaColumnContext` 和 `RetrievalContext`，作为 Agent 上下文检索的结构化数据契约。
- `backend/app/tools/metric_retriever.py`：实现确定性指标召回，从启用状态的 `metric_definitions` 中按问题关键词、指标名、展示名和描述打分。
- `backend/app/tools/schema_retriever.py`：实现表结构召回，根据指标所需表字段和问题关键词读取 `schema_metadata`。
- `backend/app/tools/context_builder.py`：组合指标和 schema 结果，输出统一的 `RetrievalContext`。
- `backend/app/agents/analysis_graph.py`：在 SQL Guard 和 Executor 前调用 `build_retrieval_context`。
- `backend/app/tools/analysis_presenter.py`：将召回结果写入 `AnalyzeResponse.source`，并增加“召回指标口径”“读取数据结构”两个执行步骤。

数据契约：

- 输入：`question: str`。
- 中间上下文：`RetrievalContext(metrics, schema_columns, tables, fields, metric_summary)`。
- 输出 API：`POST /api/analyze` 响应结构保持兼容，新增变化体现在 `source.metricDefinition`、`source.tables`、`source.fields` 和 `trace.toolCalls = 4`。
- 数据库依赖：`metric_definitions.status = 'enabled'` 的指标口径，以及 `schema_metadata` 中的业务表字段说明。

验证：

- `npm run backend:test`：18 passed，覆盖 API、指标 CRUD、retriever、SQL Guard、SQL Executor。
- `npm run test:e2e`：通过，确认 question -> FastAPI -> AgentService -> Guard -> Executor -> result 闭环仍可运行。
- `npm run frontend:build`：通过，确认前端类型和 production build 未受后端契约变化影响。

风险/后续：当前检索是关键词和规则优先的最小切片，尚未接入 embedding / pgvector；销售趋势仍使用固定 SQL 模板，下一步建议补 `query_runs` 和 `tool_calls` 持久化，之后进入 SQL Memory Retriever / Reuse Planner。
