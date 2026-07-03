# 复购率 / 城市客单价查询切片完成说明

模块：复购率 / 城市客单价查询切片

当前状态：已完成、已通过验证，等待本轮提交并推送。`/api/analyze` 已支持“最近 90 天复购率是多少？”和“每个城市的客单价是多少？”进入真实 PostgreSQL 查询链路。

业务逻辑：业务分析人员可以直接询问整体复购率或城市客单价。系统会识别用户维度或地域维度意图，基于用户、订单、支付和退款数据生成只读聚合 SQL，经过 SQL Guard、只读 Executor、结果整理和运行日志写入后返回中文业务结论。

关键代码：

- `backend/app/tools/sql_template_tools.py`：扩展 `SalesTrendParameters.metric`，新增 `repeat_purchase_rate`、`city_avg_order_value`，并渲染复购率和城市客单价 SQL。
- `backend/app/tools/schema_retriever.py`：用户维度问题会召回 `users`、`orders`、`payments`、`refunds` 等必要表结构。
- `backend/app/tools/analysis_presenter.py`：兼容 `segment_label`、`city_label`、`repeat_rate` 结果列，并生成业务用户可读摘要。
- `backend/tests/test_api.py`、`backend/tests/test_sql_template_tools.py`、`backend/tests/test_sql_generation_tools.py`：覆盖用户维度 API 和模板生成路径。

数据契约：

- `SalesTrendParameters.metric` 支持 `repeat_purchase_rate`、`city_avg_order_value`。
- `AnalyzeResponse.rows[].date` 在本切片中表示“整体复购率”或城市名称。
- `AnalyzeResponse.rows[].refundRate` 在复购率问题中承载复购率百分比，在城市客单价问题中继续承载退款率，保持当前前端表格兼容。

验证：

- `npm run backend:test`：51 passed。
- `npm run test:e2e`：backend smoke passed。
- `npm run frontend:build`：通过。

风险/后续：

- 当前复购率暂按全量已支付用户订单计算，未严格套用“最近 90 天”自然日窗口。
- V1 为兼容前端，将不同百分比指标复用到 `refundRate` 展示字段，后续应支持动态列名。
