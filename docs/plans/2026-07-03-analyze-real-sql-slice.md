# `/api/analyze` 接入真实 SQL 工具链计划

Goal: 将 `/api/analyze` 从纯 mock graph 推进到真实 PostgreSQL 查询的最小垂直切片。

当前正在做：模块已完成，`/api/analyze` 已接入真实 SQL Guard + Executor 垂直切片。

Scope:
- 包含：真实 SQL 分析 graph、Presenter、API 测试更新、文档和 handoff。
- 不包含：LLM SQL Generator、SQL Memory 检索、动态 schema retriever。

Module boundary:
- Upstream inputs: 用户问题、PostgreSQL Olist 数据、Guard/Executor 工具。
- Downstream outputs: `AnalyzeResponse`，包含真实查询 rows、summary、SQL、source、trace、steps。
- Likely touched files: `backend/app/agents`, `backend/app/services`, `backend/app/tools`, `backend/tests`, `docs/`。

Business logic:
- 用户问销售趋势时，系统执行真实 PostgreSQL 查询，而不是返回 mock 行。
- SQL 必须先经过 Guard，再交给 Executor。
- 前端仍使用原有 `POST /api/analyze` 契约。

Data contract:
- `POST /api/analyze` response contract 不变。
- `rows` 从真实 `orders/payments/refunds` 查询结果转换。

Implementation steps:
- [x] 创建计划
- [x] 添加真实分析 graph
- [x] 将 AgentService 接到真实 graph
- [x] 更新 API 测试
- [x] 运行验证
- [x] 更新 handoff 和模块文档
- [x] commit 并 push

Validation plan:
- `npm run backend:test`
- `npm run test:e2e`
- `npm run frontend:build`

Risks and open questions:
- 当前只覆盖销售趋势类问题，其他问题仍可后续扩展路由。
- SQL 模板固定，尚未接入 SQL Generator。
