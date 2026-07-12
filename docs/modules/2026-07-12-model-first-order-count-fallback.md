# 模块：模型优先订单数 Fallback

## 完成行为

- 无维度单一订单数不再在 SQL 生成入口跳过模型。
- 默认链路现在是：模型生成 -> QuerySpec 意图校验 -> 一次 Repair -> 受控 fallback。
- 当模型首次未返回 SQL，或一次 Repair 后仍无法满足订单数、支付口径与必需表要求时，才生成 `COUNT(DISTINCT orders.id)` 加 `payments.status = 'paid'` 的 fallback。
- fallback 生成后仍重新经过意图校验，随后进入 SQL Guard 和只读 Executor。

## 关键决策

- 保留模型作为主路径，以便模型能力、SQL Memory 和召回上下文真正参与简单问题，不把业务能力退化为固定模板。
- fallback 仍限定为无维度、无 Top N、无排序的已定义 `order_count`，只解决小模型无法输出基础支付订单口径时的可用性问题。

## 验证

- `backend/tests/test_analysis_graph_sql_selection.py`：`33 passed`。
- `npm.cmd run backend:test`：`210 passed, 1 warning`。
- 标准评测在 364 秒超时（exit `124`），因此未标记为通过；超时前已写完 20 题报告，结果为 `12/20` 执行成功、`60.00%` 严格成功率。

## 剩余风险

- 模型优先会增加简单订单数请求延迟；若模型输出错误，仍会经历一次 Repair 后才 fallback。
- 标准评测仍受复杂模型题耗时影响，需要单独优化评测执行方式。

## 交付

- 模块提交：`66cb945 调整订单数为模型优先生成`。
- 已推送至：`origin/main`。
