# Agent 工作流说明

## API 入口

用户通过：

```http
POST /api/analyze
```

请求体：

```json
{"question":"最近 30 天销售额按天变化如何？"}
```

返回 `AnalyzeResponse`，包含：

- `summary`
- `sql`
- `metrics`
- `rows`
- `source`
- `trace`
- `steps`

## 当前工作流

`backend/app/agents/analysis_graph.py` 是 V1 主链路。

1. 读取用户问题。
2. `build_retrieval_context()` 召回指标口径和 schema：
   - metric/schema retriever 先用 `EmbeddingAdapter` 生成问题向量。
   - pgvector 候选分与关键词、文本相似度、必需表字段等规则分融合排序。
   - 对用户、流量、优惠券、退款、毛利、商品等业务主题，会补充召回相关表字段，避免后续生成阶段缺少真实 schema。
   - embedding 或 pgvector 不可用时自动退回原文本检索，不中断分析。
   - 后端会优先从 PostgreSQL 真实外键读取 `table_relationships`，并在没有外键时基于已召回字段命名推断关系，例如 `orders.id = payments.order_id`，供模型 SQL 生成参考。
3. `retrieve_sql_memory()` 检索历史成功 SQL：
   - 优先使用 `sql_memories.question_embedding` 的 pgvector 候选分作为 `semantic_similarity`。
   - 再融合文本相似、表/指标匹配和历史成功率。
   - 向量不可用或旧 memory 没有 embedding 时回退文本相似。
4. `plan_sql_reuse()` 决定 `fast_path`、`rewrite_path` 或 `cold_path`。
5. `_select_generated_sql()` 选择 SQL：
   - 默认走确定性 SQL 生成/改写。
   - 开启 `MODEL_SQL_GENERATOR_ENABLED=true` 且 `cold_path` 时尝试模型 SQL 生成。
   - 模型 SQL Generator 的 prompt payload 只包含已召回字段、指标口径、复用计划和表关系上下文。
   - 模型失败或无 SQL 时回退确定性路径。
6. `guard_sql()` 做 SQL 安全拦截；即使 SQL 来自模型，也会经过字段存在性、只读、白名单表、`SELECT *` 和 LIMIT 等校验。
7. `execute_guarded_sql()` 用只读连接执行。
8. `present_sales_trend_result()` 组织业务结果：
   - 基于 SQL Executor 返回的真实列生成 `rows`。
   - 自动识别维度列、数值列和比例列，生成通用中文摘要和指标卡。
   - 保持普通用户只看到业务结果、SQL、来源和安全说明。
9. `QueryRunLogger` 写入 `query_runs` 和 `tool_calls`。
10. 成功查询写入或更新 SQL Memory。

## 路径含义

- `fast_path`：历史成功 SQL 可直接复用或参数化复用。
- `rewrite_path`：候选相似但不应直接复用，需要改写或重新生成。
- `cold_path`：没有可用历史 SQL，需要新生成。

## 模型路径边界

模型路径目前是可选能力：

```env
MODEL_SQL_GENERATOR_ENABLED=false
```

默认关闭。开启后只影响 `cold_path`，并且生成 SQL 仍然进入 Guard 和 Executor。
模型 prompt payload 有后端测试覆盖，验证 schema 字段、指标口径、表关系和复用计划会进入模型上下文；模型如果编造字段，仍会被 Validator / Guard 阻断。

## 日志与追踪

每次 `/api/analyze` 会写入：

- `query_runs`：问题、SQL、Guard 状态、执行状态、耗时、错误。
- `tool_calls`：SQL Memory、上下文召回、SQL 生成、Guard、Executor、Presenter、Memory 更新等摘要。
  - 上下文召回摘要包含指标数、字段数、表关系数、召回表和字段样例。
  - SQL 生成摘要包含生成路径、是否有 SQL、warning 数量和 warning 样例。
  - Guard 摘要包含放行状态、warning/error 数量和样例。

开发者接口：

- `GET /api/runs`
- `GET /api/runs/{run_id}`
- `GET /api/memories`
- `GET /api/memories/{memory_id}`

普通用户界面不展示原始工具 payload。

## 检索边界

- 普通用户响应只展示表、字段、SQL、结果和安全状态，不展示 embedding provider、向量分数或数据库连接状态。
- `semantic_score` 只作为后端 `RetrievalContext` 内部排序依据，不进入普通用户页面。
- `table_relationships` 优先来自 PostgreSQL 外键，失败或缺失时退回命名推断；它只作为后端 SQL 生成上下文，不进入普通用户页面。
- 当前混合检索已覆盖 `metric_definitions.embedding`、`schema_metadata.embedding` 和 `sql_memories.question_embedding`。
- SQL Memory 写入会同步 `question_embedding` 和 `sql_embedding`；普通用户不展示 memory 候选分数或向量状态。
