# 复杂 SQL 生成质量改进

## Completed behavior

- 对话路由和意图解析将“成交 / 交易 / 金额”视为明确业务数据对象；`2017 年成交额是多少？` 不再进入普通聊天或错误澄清。
- 新增 migration `016_complex_sql_accuracy_semantic_contracts.sql`，声明已支付订单成交额与订单数、订单商品整体毛利率，以及 `category_sales_ranking` 的 v2 输出别名。
- 合同仅提供来源表/字段、过滤、聚合、粒度和输出形态，继续由模型生成 SQL；未引入固定 SQL。
- migration 已应用至本地 `local_data_agent` PostgreSQL。

## Key decisions

- “成交额”在本评测数据集中的定义为已支付订单成交额：按 `payments.order_id` 去重后关联订单，避免多笔支付放大订单金额。
- 品类销售额排行的稳定输出别名更新为 `sales_amount`，以与结果合同和评测数据集一致；采用新版本，未改写旧合同。
- SQL 安全边界不变：Query Plan/Inspector 诊断，SQL Guard，`EXPLAIN` 和只读 Executor 均保留。

## Validation

- `.venv\\Scripts\\python.exe -m pytest backend/tests/test_question_intent_parser.py backend/tests/test_dialogue_router.py backend/tests/test_semantic_resolver.py backend/tests/test_query_planner.py backend/tests/test_db_migrations.py -q`
  - `51 passed`
- `.venv\\Scripts\\python.exe backend/scripts/init_db.py`
  - migration `016_complex_sql_accuracy_semantic_contracts.sql` 已成功应用。
- 单样本 `speed_006`：`1/1` 执行、严格和结构化行正确。
- `npm.cmd run eval:standard`
  - `19/20` 执行成功，`95%` 严格成功率。
- 结构化 20 条回归：`eval/reports/sql_accuracy_20_complex_contracts_final_20260722.json`
  - 执行成功 `20/20`，较修改前 `19/20` 提升 1 条。
  - 结构化行匹配 `15/20`（`75%`），较修改前 `12/20`（`60%`）提升 15 个百分点。
  - Memory fast path `4/20`（`20%`）；本模块针对非命中 Memory 的生成质量，未以提升 Memory 命中为目标。
  - 平均端到端耗时 `21.69s`，旧报告为 `20.80s`；模型路径存在自然波动，不能据此宣称性能提升。
- `git diff --check` 通过。

## Remaining risks and follow-up

- `speed_008`、`speed_009`：支付品类排行仍可能未遵守订单级去重与销售额口径。
- `speed_010`、`speed_011`：未要求支付条件的品类销售额仍可能错误引入支付口径或排序口径。
- `speed_012`：模型将“按商品明细”误作逐商品列表，而评测要求整体毛利率单行结果。
- 下一轮应为上述三类问题增加可解释的 Inspector 诊断和一次定向 Repair，再复跑同一 20 条集；不得增加固定 SQL 回退。

## Delivery

- 本模块与工作区已有未提交的 SQL Memory/分层校验改动共享 `Query Planner`、测试和 handoff 文件，当前无法安全区分并单独暂存。未执行 commit/push，避免将用户或前序未提交改动一并提交。
