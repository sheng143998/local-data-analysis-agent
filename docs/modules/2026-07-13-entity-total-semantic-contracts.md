# Entity Total Semantic Contracts

## Completed behavior

- 新增订单商品、支付、退款、评价、流量、优惠券和优惠券使用记录的基础实体总量契约。
- SQL Prompt 现在保留 resolved contracts 的定义、来源表、字段和聚合，供模型按业务实体生成 SQL。
- 未增加固定 SQL 或绕过 Inspector、Guard、Executor。

## Validation

- migration `011` 已应用，数据库确认 10 个启用基础实体契约。
- resolver/planner/model payload focused `16 passed`。
- authenticated `database_001` 至 `database_010`：执行成功 `7/10`，严格成功 `3/10`，答案匹配 `3/10`；前一批为 `7/10`、`2/10`、`2/10`。

## Remaining risks

- 基础总量契约只改善该类问题；复杂业务公式仍需受审核契约、Trusted SQL 与模型改进。
