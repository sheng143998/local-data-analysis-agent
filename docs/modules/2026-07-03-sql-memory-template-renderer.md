# 模块：SQL Memory 参数化模板与时间范围改写

当前状态：模块已完成，已通过 `npm run backend:test`、`npm run test:e2e` 和 `npm run frontend:build` 验证，已提交并推送到 GitHub。

业务逻辑：用户提出“最近 7 天销售额是多少？”、“最近 30 天销售额按天变化如何？”这类问题时，系统会解析时间范围，生成 `days` 参数，并渲染销售趋势 SQL。即使命中高置信 SQL Memory，也会按当前问题重新渲染 SQL，让 `fast_path` 从完全固定 SQL 复用升级为参数化复用。查询成功后，`days` 和 `granularity` 会写入 `sql_memories.parameters`，便于后续审计和模板扩展。

关键代码：

- `backend/app/tools/sql_template_tools.py`：新增 `SalesTrendParameters`、`parse_sales_trend_parameters` 和 `render_sales_trend_sql`。
- `backend/app/agents/analysis_graph.py`：在检索和执行前解析当前问题时间范围，并用渲染后的 SQL 进入 Guard / Executor。
- `backend/app/schemas/memories.py`：为 `SqlMemoryUpsert` 增加 `parameters`。
- `backend/app/db/repositories/memory_repository.py`：写入和更新 `sql_memories.parameters`。
- `backend/app/tools/sql_memory_tools.py`：成功写入 SQL Memory 时携带参数；高置信复用计划标记为 `parameter_rewrite`。
- `backend/tests/test_sql_template_tools.py`：覆盖最近 N 天、一周、一个月、三个月和大范围边界。

数据契约：`SalesTrendParameters` 当前包含 `days` 和 `granularity`；`sql_memories.parameters` 当前写入 `{"days": N, "granularity": "day"}`；`SqlReusePlan.selected_sql` 在 `fast_path` 命中时会被当前问题的渲染 SQL 覆盖，确保复用 SQL 与用户问题时间范围一致。

验证：`npm run backend:test` 已通过，28 passed，覆盖 API、指标 CRUD、retriever、runs、SQL Guard、SQL Executor、SQL Memory 和 SQL 模板渲染；`npm run test:e2e` 已通过，确认 question -> FastAPI -> AgentService -> Guard -> Executor -> result 闭环仍可运行；`npm run frontend:build` 已通过，确认前端构建未受后端模板改动影响。`FastAPI TestClient` 仍有 `StarletteDeprecationWarning`，不影响功能。

风险/后续：当前“最近 N 天”用 `LIMIT N` 表示最近 N 个有交易日期，不是严格自然日窗口；后续应支持品类、城市、Top N、按月粒度，并把中置信候选接入 SQL Rewriter。
