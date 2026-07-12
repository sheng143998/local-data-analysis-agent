# Backend

本目录承载本地数据分析 Agent 的 FastAPI 后端。

当前最小闭环：

1. `POST /api/analyze` 接收自然语言问题。
2. `AgentService` 调用 LangGraph 正式编排。
3. graph 经过上下文召回、RAG rerank、SQL Memory 候选规划、候选 SQL 校验、模型生成/改写、SQL Guard、只读执行器和执行错误修复闭环。
4. API 返回前端需要展示的分析摘要、最终 SQL、表格数据和追溯信息。

核心模块：

- `agents/`: LangGraph 节点与路由
- `tools/`: 模型 SQL 生成、校验、Guard、执行器、SQL Memory 检索
- `db/`: PostgreSQL/pgvector 连接、迁移、仓储
- `services/`: 业务编排与响应塑形
- `schemas/`: Pydantic API 契约

## 当前 SQL 生成与修复闭环

已实现 **SQL Intent Validator / Repair Loop**，位置在 `generate_model_sql` 之后、`guard_sql` 之前：

1. `validate_generated_sql_intent` 节点校验模型 SQL 是否覆盖当前问题需要的表、指标 token、维度 token、时间粒度和 Top N / LIMIT。
2. `analysis_graph._verify_memory_sql()` 与模型 SQL 校验共用 requirement/feature 规则，减少 fast 复用与模型路径的判断漂移。
3. `repair_model_sql` 节点在第一次校验失败时，把错误列表、原 SQL、召回 schema/metric/table_relationships 和用户问题回传模型修复。
4. 修复上限当前为 1 次；超过上限直接返回 `model_error`，并在 `tool_calls.analysis_graph.select_generated_sql.output_payload.intent_verification` 中记录失败原因与修复次数。
5. 已补 focused tests 覆盖：指标不匹配、意图校验通过、修复后失败阻断、repair payload、CTE 查询通过 Guard。
6. `execute_sql` 执行失败后会分类数据库错误，如 `group_by`、`missing_column`、`missing_table`、`type_cast`、`division_by_zero`、`syntax` 和 `runtime`；若还未触发执行错误修复，则带着原 SQL、错误类别和友好摘要回到 `repair_model_sql`，修复后重新经过意图校验、Guard 和执行。

## 当前 RAG 优化

`build_retrieval_context()` 在 metric/schema 粗召回后接入规则 rerank：

1. 识别指标、表、字段和时间意图。
2. 对 metric 候选融合原始检索分、语义分、指标意图、表字段意图和时间意图。
3. 对 schema 候选优先保留指标必需字段、时间字段和 join key，并限制 prompt 上下文字段规模。
4. rerank 诊断写入开发者 `tool_calls`，普通用户页面不展示内部评分。

下一步建议扩展评估集和失败归因报表，把失败分成召回缺表、指标缺失、模型字段编造、Guard 拦截、执行错误修复失败、结果为空、SQL 与问题不一致。
