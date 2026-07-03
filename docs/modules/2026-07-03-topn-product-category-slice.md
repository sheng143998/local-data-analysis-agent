# Top N 商品/品类销售额查询切片完成说明

模块：Top N 商品/品类销售额查询切片

当前状态：已完成、已通过验证，等待本轮提交并推送。`/api/analyze` 已支持“销售额最高的前 10 个商品是什么？”和“哪个商品品类销售额最高？”进入真实 PostgreSQL 查询链路。

业务逻辑：业务分析人员可以直接询问商品或品类销售排行。系统会识别 Top N、商品/品类维度和销售额指标，生成聚合 SQL，经过 SQL Guard 和只读 Executor 后返回排行结论、SQL、结果表、来源字段和可信说明。

关键代码：

- `backend/app/tools/sql_template_tools.py`：扩展 `SalesTrendParameters.metric`，新增 `top_product_sales`、`top_category_sales` 和 `limit` 参数，并渲染商品/品类销售额排行 SQL。
- `backend/app/tools/schema_retriever.py`：商品/品类问题会召回 `order_items`、`products`、`payments` 等必要表结构。
- `backend/app/tools/analysis_presenter.py`：将排行结果兼容映射到现有 `AnalyzeResponse.rows`，并生成面向业务用户的中文摘要。
- `frontend/src/pages/ChatPage.tsx`：把聊天结果表头从固定“日期/日销售额”调整为更通用的“维度/销售额”。

数据契约：

- `SalesTrendParameters.model_dump()` 现在包含 `days`、`granularity`、`metric`、`limit`。
- `AnalyzeResponse.rows[].date` 在趋势问题中表示日期/月度，在排行问题中表示商品 ID 或品类名称，保证前端兼容。
- `/api/analyze` 响应结构不变，普通用户界面不展示 SQL Memory 评分或内部工具 payload。

验证：

- `npm run backend:test`：38 passed。
- `npm run test:e2e`：backend smoke passed。
- `npm run frontend:build`：通过。

风险/后续：

- V1 当前使用 `order_items.price` 计算商品/品类销售额，避免订单总额在多商品订单中重复计算。
- 前端仍复用兼容表格，后续可为排行类问题增加动态列标题和图表类型。
