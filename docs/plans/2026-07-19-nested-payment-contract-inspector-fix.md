# 支付子查询合同校验修复

## Goal

修复品类订单商品数与销售额查询被错误拒绝的问题：允许安全的 `payments` 去重子查询满足合同字段要求，并将排序语义排除在 WHERE 过滤约束之外。

## Scope

- 为 Inspector 增加嵌套单表 SELECT 中无表前缀字段的安全归属识别。
- 将“升序 / 降序 / 排序”类文本从业务过滤中排除。
- 用截图问题的首次安全候选 SQL 覆盖 Inspector、Planner 与真实 API 回归。

## Out of scope

- 不接受直接 Join `payments` 后重复累计订单金额或订单商品明细。
- 不放宽 Guard、EXPLAIN 或只读执行器。

## Implementation steps

- [x] 修复字段归属与结构性排序过滤规则。
- [x] 添加 focused tests。
- [x] 执行真实截图问题 API 回归。
- [x] 更新记录、提交与推送。

## Validation plan

- Inspector/Planner/Graph focused pytest。
- 原始问题经真实 API 返回 Guard 放行 SQL 与结果。

## Risks

- 嵌套字段归属只应在其局部 SELECT 中仅有一个真实表时推断，避免多表歧义被误认为合同字段。
