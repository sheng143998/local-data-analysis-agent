# Query Plan And Context Pack

## Completed behavior

- `QueryPlan` 从 QuerySpec、已解析语义契约和 intent 构造实体、度量、维度、过滤、排序、limit 和结果形态。
- Plan 进入 intent、Graph、Context Builder 和 SQL generator payload；Context Pack 只补入计划需要的实体表。
- 未知概念保持开放式候选，不在 planner 中猜测公式或执行 SQL。

## Validation

- focused `46 passed`。
- 后端全量 `238 passed, 1 warning`。

## Remaining risks

- Inspector 尚未独立对齐 Query Plan；下一模块将把实体、度量、维度和输出形态作为执行前检查项。
