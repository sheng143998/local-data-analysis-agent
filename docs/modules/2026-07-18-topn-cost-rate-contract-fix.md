# Top N、成本与比率合同修复

## Completed behavior

- Planner 会剔除前 N、排行、排序和时间粒度等结构词，防止它们作为 WHERE filter 被 Inspector 错误拦截。
- 新增 `014` 迁移，登记成本总额、退款订单率与复购用户数的审核公式、来源表和字段。
- 比率展示按数据库 0 到 1 比例转换为百分数。

## Validation

- `init_db.py` 已应用 `014_cost_rate_repeat_semantic_contracts.sql`。
- Planner/Inspector/Presenter focused：`19 passed`。
- 真实五题报告：`contract_sql_validation_5cases_after_fix_20260718.json`，执行 `3/5`、严格 `1/5`、答案 `2/5`。`database_022` 的“前5个”伪 filter 已消失，但模型仍未输出合同别名/排序；`028` 合同已进入链路但模型口径仍错；`035` 模型未输出退款率 SQL；`043` 答案匹配但 HAVING 尚未 AST 强制。

## Follow-up

- 为合同维度建立物理字段别名映射，并为复购合同增加 HAVING AST 约束。
