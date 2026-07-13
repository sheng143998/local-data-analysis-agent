# Entity Total Semantic Contracts

## Goal

根据 authenticated benchmark 的失败证据，补齐基础实体总量契约并将已解析契约传入 SQL Prompt，避免模型把商品、支付、退款、评价等总数错误生成为订单总数。

## Scope

- 新增基础实体总量的版本化语义契约 seed。
- 透传契约定义、表、字段和聚合到模型 payload。
- 测试合同摘要和 Query Plan 实体约束。

## Out of scope

- 不增加固定 SQL、直接执行 SQL 或降低 Guard。

## Implementation steps

- [ ] 增加契约 seed migration。
- [ ] 在 SQL payload 保留 resolved contracts。
- [ ] 测试、真实基础表核对、评测抽样、文档和提交。

## Validation plan

- semantic resolver/query planner/model payload focused tests；真实只读表总量核对；authenticated eval 抽样。

## Risks

- 契约是业务定义而非 SQL 模板，复杂指标仍由 Planner/模型/Inspector 协作完成。
