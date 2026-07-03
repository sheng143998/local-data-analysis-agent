# 模块完成说明：`/api/analyze` 接入真实 SQL 工具链

模块：`/api/analyze` 真实 SQL 垂直切片

当前状态：已完成，销售趋势问题已从纯 mock 返回升级为真实 PostgreSQL 查询，已通过测试并准备提交。

业务逻辑：
- 用户通过 `/api/analyze` 提问销售趋势时，后端使用固定 SQL 模板查询真实 Olist PostgreSQL 数据。
- SQL 先经过 `guard_sql`，再交给 `execute_guarded_sql`。
- Presenter 将真实查询结果转换为前端兼容的 `AnalyzeResponse`。
- 当前仍未接入 LLM SQL Generator 和 SQL Memory，只完成真实工具链的最小垂直切片。

关键代码：
- `backend/app/agents/analysis_graph.py`：串起 SQL 模板、Guard 和 Executor。
- `backend/app/tools/analysis_presenter.py`：将执行结果组织为业务摘要、指标、来源、步骤和表格行。
- `backend/app/services/agent_service.py`：从 mock graph 切换到真实 analysis graph。
- `backend/tests/test_api.py`：验证 `/api/analyze` 返回真实 PostgreSQL 结果。
- `backend/tests/smoke_api.py`：smoke 文案更新为 Guard -> Executor。

数据契约：
- `POST /api/analyze` response contract 不变。
- `rows` 来自真实 `orders`、`payments`、`refunds` 查询。
- `source.security` 包含 SQL Guard 通过说明。

验证：
- `npm run backend:test`
- `npm run test:e2e`
- `npm run frontend:build`

风险/后续：
- 当前只支持销售趋势固定 SQL 模板。
- 下一步应接入 schema/metric retriever，并根据问题选择 SQL 模板或生成路径。
- 还未写入 `query_runs` 和 `tool_calls`。
