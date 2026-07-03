# 退款率 / 支付成功率查询切片完成说明

模块：退款率 / 支付成功率查询切片

当前状态：已完成、已通过验证，等待本轮提交并推送。`/api/analyze` 已支持“哪个商品品类退款率最高？”和“每个支付方式的成功率是多少？”进入真实 PostgreSQL 查询链路。

业务逻辑：业务分析人员可以直接询问退款率最高的品类或不同支付方式的成功率。系统会识别指标口径和聚合维度，生成只读聚合 SQL，经过 SQL Guard、只读 Executor、结果整理和运行日志写入后返回中文业务结论。

关键代码：

- `backend/app/tools/sql_template_tools.py`：扩展 `SalesTrendParameters.metric`，新增 `category_refund_rate`、`payment_success_rate`、`payment_failure_rate`，并渲染退款率和支付成功率 SQL。
- `backend/app/tools/schema_retriever.py`：退款类问题会召回 `refunds`、`order_items`、`products`、`payments` 等必要表结构。
- `backend/app/tools/analysis_presenter.py`：兼容 `refund_rate`、`success_rate`、`failure_rate` 结果列，并生成业务用户可读摘要。
- `backend/tests/test_api.py`、`backend/tests/test_sql_template_tools.py`、`backend/tests/test_sql_generation_tools.py`：覆盖复杂指标 API 和模板生成路径。

数据契约：

- `SalesTrendParameters.metric` 支持 `category_refund_rate`、`payment_success_rate`、`payment_failure_rate`。
- `AnalyzeResponse.rows[].date` 在复杂指标问题中表示品类或支付方式。
- `AnalyzeResponse.rows[].refundRate` 在退款率问题中表示退款率，在支付问题中表示成功率或失败率，保持前端兼容。

验证：

- `npm run backend:test`：43 passed。
- `npm run test:e2e`：backend smoke passed。
- `npm run frontend:build`：通过。

风险/后续：

- 退款率当前按“存在退款记录的订单数 / 有效订单数”计算，后续可扩展为退款金额口径。
- 支付成功率当前基于 `payments.status = 'paid'`，当前真实数据以 paid 为主，后续可结合更多失败支付状态增强分析价值。
