# Schema + Metric Retriever 最小切片计划

## Goal

让 `/api/analyze` 在执行 SQL 前，先从 PostgreSQL 的 `metric_definitions` 和 `schema_metadata` 召回业务指标与数据结构上下文，减少硬编码上下文，为后续 SQL Generator / SQL Memory 打基础。

## 当前正在做

当前正在做：Schema + Metric Retriever 最小切片已完成，等待提交并推送。

## Scope

包含：

- 新增检索输出 Pydantic schema。
- 从 `metric_definitions` 按业务问题做关键词召回。
- 从 `schema_metadata` 按指标所需表和字段召回表结构。
- 将召回结果接入 `analysis_graph.py` 和 `AnalyzeResponse.source`。
- 增加 focused backend tests。

不包含：

- embedding / pgvector 相似度检索。
- LLM SQL Generator / Rewriter。
- SQL Memory 复用路径。
- 前端页面改造。

## Module Boundary

- 上游输入：用户自然语言问题、PostgreSQL 元数据表。
- 下游输出：`RetrievalContext`、`AnalyzeResponse.source`、Agent steps/trace。
- 可能触达文件：
  - `backend/app/schemas/retrieval.py`
  - `backend/app/tools/metric_retriever.py`
  - `backend/app/tools/schema_retriever.py`
  - `backend/app/tools/context_builder.py`
  - `backend/app/agents/analysis_graph.py`
  - `backend/app/tools/analysis_presenter.py`
  - `backend/tests/test_retrieval_tools.py`
  - `backend/tests/test_api.py`

## Business Logic

业务分析人员提问“最近 30 天销售额按天变化如何？”时，系统应先识别“销售额、订单数、退款率、客单价”等相关业务指标，再根据这些指标读取 `orders`、`payments`、`refunds` 等表字段说明。回答仍保持普通用户友好的自然语言、SQL、结果表和来源说明，但来源中的指标口径、表、字段应由元数据召回结果生成。

## Data Contract

- `MetricContext`
  - `metric_name`
  - `display_name`
  - `description`
  - `formula`
  - `required_tables`
  - `required_fields`
  - `score`
- `SchemaColumnContext`
  - `table_name`
  - `column_name`
  - `data_type`
  - `description`
  - `business_meaning`
- `RetrievalContext`
  - `metrics`
  - `schema_columns`
  - `tables`
  - `fields`
  - `metric_summary`

## Implementation Steps

任务清单：

- [x] 读取 handoff 和现有 analyze 链路。
- [x] 创建本计划文档。
- [x] 实现检索 schema 和工具函数。
- [x] 接入 `analysis_graph.py` 与 presenter。
- [x] 增加测试并运行验证。
- [x] 更新模块完成文档和 handoff。
- [~] commit 并 push。

## Validation Plan

- `npm run backend:test`：已通过，18 个测试通过。
- `npm run test:e2e`：已通过，FastAPI smoke 闭环通过。
- `npm run frontend:build`：已通过，Vite production build 成功。

## Risks and Open Questions

- 当前是确定性关键词召回，不代表最终语义检索能力；后续需要接 embedding / pgvector。
- 当前销售趋势仍使用固定 SQL 模板，retriever 只负责提供上下文，不负责生成 SQL。
