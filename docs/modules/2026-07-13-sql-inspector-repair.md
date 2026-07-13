# SQL Inspector And Categorized Repair

## Completed behavior

- 新增 AST 驱动 Inspector，检查 SQL 是否覆盖 Query Plan 实体、排行排序、Top N limit 和时间过滤。
- Inspector issue 以 `missing_table/missing_order/missing_limit/time_range/syntax` 分类进入已有 repair context。
- 不匹配 SQL 在 Guard 和 Executor 前进入有限 repair；Guard 继续是最终安全边界。

## Validation

- focused `35 passed`。
- 后端全量 `240 passed, 1 warning`。

## Remaining risks

- 当前不含 EXPLAIN 和受控探针查询；复杂 CTE/别名只能保守检查。
