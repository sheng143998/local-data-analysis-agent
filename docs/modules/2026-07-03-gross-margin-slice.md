# 毛利率查询切片完成说明

模块：毛利率查询切片

当前状态：已完成、已通过验证，等待本轮提交并推送。`/api/analyze` 已支持“最近 30 天毛利率最高的商品品类是什么？”进入真实 PostgreSQL 查询链路。

业务逻辑：业务分析人员可以直接询问毛利率最高的商品品类。系统会识别毛利率意图，基于商品明细销售额和商品成本表计算品类毛利率，经过 SQL Guard、只读 Executor、结果整理和运行日志写入后返回中文业务结论。

关键代码：

- `backend/app/tools/sql_template_tools.py`：扩展 `SalesTrendParameters.metric`，新增 `category_gross_margin`，并渲染品类毛利率 SQL。
- `backend/app/tools/schema_retriever.py`：毛利率问题会召回 `order_items`、`products`、`product_costs`、`payments` 等必要表结构。
- `backend/app/tools/analysis_presenter.py`：兼容 `gross_margin` 结果列，并生成面向业务用户的毛利率排行摘要。
- `backend/tests/test_api.py`、`backend/tests/test_sql_template_tools.py`、`backend/tests/test_sql_generation_tools.py`：覆盖毛利率 API 和模板生成路径。

数据契约：

- `SalesTrendParameters.metric` 支持 `category_gross_margin`。
- `AnalyzeResponse.rows[].date` 在本问题中表示商品品类。
- `AnalyzeResponse.rows[].refundRate` 在本问题中承载毛利率百分比，保持当前前端表格兼容。

验证：

- `npm run backend:test`：46 passed。
- `npm run test:e2e`：backend smoke passed。
- `npm run frontend:build`：通过。

风险/后续：

- 当前成本口径使用 `product_costs.unit_cost`，该字段由导入脚本基于商品重量合成生成，后续可替换为真实成本数据。
- V1 为兼容前端，将毛利率复用到 `refundRate` 展示字段，后续应支持动态列名。
