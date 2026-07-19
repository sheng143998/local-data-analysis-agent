# 模块：品类订单商品数与销售额排行失败修复

## 已完成行为

- 新增 `category_item_sales_ranking` 版本化语义合同：已支付订单内按商品品类统计 `order_items.id` 与 `order_items.price`，按订单商品数量降序，并支持用户给定的 Top N。
- 复合合同命中后替代泛化的 `sales_amount` 与 `category_item_count_ranking` 合同，避免 `orders.total_amount` 来源约束和品类商品明细口径冲突。
- “商品品类 / 品类 / 类目 / 分类”统一为 `category`；启发式意图不再将“商品品类”同时识别为 `product`。
- 已支付筛选来自已确认合同也会生成订单粒度与支付去重策略，模型仍须通过 Inspector、Guard、EXPLAIN 与只读 Executor。

## 关键决策

- 品类销售额采用订单商品明细售价之和，不将整单金额分配到多个品类。
- 不增加固定 SQL 模板，不放宽 Guard，也不以模型超时为由跳过合同校验。
- SQL 模型的云端超时与空响应仍按照既有安全策略失败；本模块保证正确候选可以通过确定性链路。

## API 与数据影响

- 未变更 API 或前端类型。
- 新增迁移 `015_category_item_sales_ranking_contract.sql`，向 `semantic_contracts` 添加一个启用的版本化合同；迁移可重复执行。

## 验证

- `python -m pytest backend/tests/test_question_intent_parser.py backend/tests/test_semantic_resolver.py backend/tests/test_query_planner.py backend/tests/test_sql_inspector.py backend/tests/test_analysis_graph_sql_selection.py -q`：`71 passed`。
- `python backend/scripts/init_db.py`：迁移 `015_category_item_sales_ranking_contract.sql` 已应用。
- 真实本地只读验证：目标问题只解析到 `category_item_sales_ranking`；Inspector 无问题、Guard 放行、EXPLAIN 成功、Executor 成功返回 10 行。首行是 `cama_mesa_banho`、订单商品数 `11115`、销售额 `1036988.68`。
- `npm.cmd run frontend:build`：通过；仅有既有 bundle 大小提示。
- `git diff --check`：通过。

## 剩余风险与后续

- 云端 SQL 模型仍可能在首次生成或修复时超时、返回非 JSON 或缺少 `sql`；需要独立提升模型路由/可用性，不能把固定 SQL 写回主链路。
- 合同替代仅在特异合同显式声明 `replaces_contract_keys` 时发生；新增复合指标时应同时声明其前置条件与被覆盖的泛化口径。

## 交付

- 实现提交：`46cd7a6`（`修复品类商品排行合同`）。
- 推送：已推送至 `origin/main`。
