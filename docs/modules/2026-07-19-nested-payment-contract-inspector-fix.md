# 模块：支付子查询合同校验修复

## 已完成行为

- Inspector 现在能在局部仅含一个真实表的嵌套 SELECT 中识别无前缀字段归属。例如 `SELECT DISTINCT order_id FROM payments WHERE status = 'paid'` 正确满足 `payments.order_id` 和 `payments.status` 合同字段及过滤条件。
- Planner 不再将“升序 / 降序 / 排序”等结构性排序表达式保留为 WHERE 业务过滤。
- 对截图问题，模型首次生成的支付去重 SQL 会被直接放行；不会因误拦截进入修复后退化为直接 Join `payments` 的重复累计风险 SQL。

## 根因

运行 `2e4a0aac-8228-469c-bf61-cc0bb52b4628` 的首次候选 SQL 已通过 `SELECT DISTINCT order_id FROM payments WHERE status = 'paid'` 安全去重，但旧 Inspector 只能将无前缀字段映射给整条 SQL 的单表查询，无法识别嵌套单表 `payments` 作用域，错误判定缺少合同字段。

## 验证

- `python -m pytest backend/tests/test_sql_inspector.py backend/tests/test_query_planner.py backend/tests/test_analysis_graph_sql_selection.py backend/tests/test_comprehensive_agent_cases.py -q`：`56 passed`。
- 真实 `POST /api/analyze` 回归原问题“订单商品数量最多的前 10 个商品品类是什么？展示品类、订单商品数量和销售额。”：HTTP `200`，Guard 放行，PostgreSQL 只读执行成功，返回 10 行。首行 `cama_mesa_banho`：订单商品数 `11115`，销售额 `1036988.68`。

## 风险

- 局部字段归属只在所属 SELECT 中恰有一个真实表时启用；多表局部作用域仍不会猜测字段归属。
- 外部 SQL 模型仍可能超时或返回空 SQL；该类外部失败保留既有安全终止，不执行数据库。

## 交付

- 提交与推送结果待本模块 Git 操作完成后补充。
