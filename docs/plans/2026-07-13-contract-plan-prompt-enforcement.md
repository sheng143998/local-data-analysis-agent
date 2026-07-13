# Contract And Plan Prompt Enforcement

## Goal

根据完整 benchmark 失败分类，使模型明确优先遵守已绑定 Semantic Contract 和 Query Plan，避免无关 payments/context 约束阻断基础实体聚合。

## Scope

- 在 SQL system prompt 明确契约、Plan、schema 的优先级与 snapshot 聚合规则。
- Inspector 对实体覆盖只使用 Query Plan entities，保留 QuerySpec 作为附加业务约束。
- 补充基础实体总量 prompt 和 Inspector 回归。

## Out of scope

- 不增加按问题写死的 SQL，不放宽 Guard 或删除支付口径校验。

## Implementation steps

- [ ] 增强契约/Plan Prompt。
- [ ] 修正 Inspector 实体约束来源。
- [ ] 测试、authenticated 小批评测、文档、commit。

## Validation plan

- model payload/Inspector/Graph focused tests，authenticated 前 10 条评测。

## Risks

- 复杂支付销售额仍必须绑定 payments；只针对 snapshot contract 避免引入无关表。
