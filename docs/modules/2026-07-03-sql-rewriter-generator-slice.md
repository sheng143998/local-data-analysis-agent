# SQL Rewriter / Generator 最小切片完成说明

模块：SQL Rewriter / Generator 最小切片

当前状态：已完成、已通过验证，等待本轮提交并推送。`/api/analyze` 已支持“最近 90 天每月订单数是多少？”进入真实 PostgreSQL 查询链路。

业务逻辑：业务分析人员可以用自然语言提出按月订单数问题。系统会识别时间范围、月度粒度和订单数指标，在 SQL Memory 规划后选择模板生成或确定性改写 SQL，再经过 SQL Guard、只读 Executor、结果整理和运行日志写入。

关键代码：

- `backend/app/tools/sql_template_tools.py`：扩展 `SalesTrendParameters`，新增 `granularity` 和 `metric` 解析，支持 `DATE_TRUNC('month', ...)` 月度时间桶。
- `backend/app/tools/sql_generation_tools.py`：新增 `generate_or_rewrite_sales_sql`，按 `reuse_plan.path_type` 输出 `template_render` 或 `deterministic_rewrite`。
- `backend/app/agents/analysis_graph.py`：把生成/改写节点接入 Memory 规划之后、Guard 之前，并把生成路径写入 `tool_calls`。
- `backend/app/tools/analysis_presenter.py`：根据 SQL 和问题生成更贴近业务口径的中文摘要。

数据契约：

- 新增 `backend/app/schemas/sql_generation.py`，定义 `GeneratedSql`。
- `SalesTrendParameters.model_dump()` 现在写入 `days`、`granularity`、`metric`。
- `/api/analyze` 的响应结构不变，前端无需改动。

验证：

- `npm run backend:test`：33 passed。
- `npm run test:e2e`：backend smoke passed。
- `npm run frontend:build`：通过。

风险/后续：

- 当前“最近 90 天每月”用最近 3 个有交易月份表达，不是严格自然日过滤窗口。
- Rewriter 仍是确定性最小切片；后续需要接入统一 ModelAdapter、prompt 模板和 20 个标准问题评估集。
