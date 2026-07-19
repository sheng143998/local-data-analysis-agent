# 模块：十个多表查询逐条验证报告

## 执行方式

十条均按编号顺序单独运行，未使用并发或批量评测。每条标准 SQL 都经过 Query Plan/Inspector、SQL Guard、EXPLAIN 和 PostgreSQL 只读执行。第 1、2、3 条还通过真实 `AgentService` 触发模型生成链路。

| # | 业务问题 | 关系表 | 结果 |
| --- | --- | --- | --- |
| 1 | 2017 年已支付订单数 | `orders` + `payments` | 真实链路通过，`45,101`。修复后 SQL 使用 `EXISTS` 与订单去重。 |
| 2 | 2017 年已支付订单金额 | `orders` + `payments` | 真实链路通过，`7,249,746.73`；未发生多支付重复累计。 |
| 3 | 销售额最高的前 5 个品类 | `order_items` + `products` | 模型链路双次读取超时；合同 SQL 逐条验证通过，首位 `beleza_saude`，`1,258,681.34`。 |
| 4 | 按订单商品数排行的前 10 个品类及销售额 | `orders` + `payments` + `order_items` + `products` | 通过，首位 `cama_mesa_banho`：`11,115` 件、`1,036,988.68`。 |
| 5 | 订单商品明细毛利率 | `order_items` + `product_costs` | 通过，`82.65%`。 |
| 6 | 退款订单率 | `refunds` + `orders` | 通过，`1.24%`。 |
| 7 | 订单数最多的前 5 个城市 | `users` + `orders` | 通过，首位 `sao paulo`：`15,540` 单。 |
| 8 | 至少 20 单且平均订单金额最高的前 5 个城市 | `users` + `orders` | 通过，首位 `gaspar`：平均 `387.787`，`30` 单。 |
| 9 | 复购用户数 | `users` + `orders` | 初始 Guard 误拦截 `COUNT(*)`；修复后通过，结果 `0`。 |
| 10 | 访问用户到下单用户转化率 | `traffic_events` + `orders` | 通过，流量表为空，`NULLIF` 保护后结果为 `NULL`，未发生除零错误。 |

## 修复项

- `已支付`、`已付款`、`支付成功`、`成交`等短过滤词现在统一为 `payments.status = 'paid'`。此前模型已生成正确的 `EXISTS` 谓词，但 Inspector 仍要求中文短语，导致第 1 条被错误拒绝。
- SQL Guard 现在只拒绝投影通配符 `SELECT *` 和 `table.*`，允许安全的 `COUNT(*)` 聚合。此前第 9 条因将聚合参数误判为投影通配符而被阻断。

## 验证

- `python -m pytest backend/tests/test_question_intent_parser.py backend/tests/test_semantic_resolver.py backend/tests/test_query_planner.py backend/tests/test_sql_inspector.py backend/tests/test_sql_validation_tools.py backend/tests/test_analysis_graph_sql_selection.py -q`：`85 passed`。
- `npm.cmd run frontend:build`：通过；仅保留既有 bundle 大小提示。
- `git diff --check`：通过。

## 风险

- 第 3 条真实模型生成连续两次在约 120 秒后读取超时，候选 SQL 为空；这是云端模型可用性问题，不是合同、Guard 或数据库失败。其手工生成的受合同约束 SQL 已通过全部确定性验证。
- 后续应单独优化模型路由和超时可观测性，不能以固定 SQL 代替模型主链路。

## 交付

- 实现提交：`074d390`（`验证并修复多表查询链路`）。
- 推送：已推送至 `origin/main`。
