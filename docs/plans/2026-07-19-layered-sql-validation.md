# 分层 SQL 校验重构

## Goal

将 SQL 生成链路从“计划细节不一致即阻断”重构为分层决策：只读安全和确定性数据库错误保持阻断，业务合同与 SQL 形态作为一次修复建议和可观测 warning；评测以结果语义而非实现细节作为严格准确率依据。

## Scope

- Inspector 保留 AST 诊断和修复规则，但不再作为最终执行拒绝条件。
- Graph 对 Inspector 问题最多发起一次 Repair；Repair 后仍有业务形态 warning 时，只要意图校验、Guard、EXPLAIN 和只读执行通过即可返回结果。
- 修正 Query Plan 对无明确合同排序的默认维度排序要求。
- Eval 保留表/关键词覆盖指标，但从严格成功和语义准确率判定中移除。
- 新增回归测试，并以相同 20 条结构化样本顺序评测效果。

## Out of scope

- 不放宽 SQL Guard 的只读、表字段白名单、危险表达式和资源限制。
- 不移除意图安全校验、EXPLAIN 或只读 Executor。
- 不为业务问题添加固定 SQL 模板。

## Implementation steps

- [ ] 标记 Inspector 的建议性问题并调整 Graph 选择逻辑。
- [ ] 修正 Query Plan 默认排序与 Eval 严格判定。
- [ ] 补充分层校验的 focused tests。
- [ ] 顺序完成 20 条结构化评测并对比基准。
- [ ] 完成回归、记录、提交与推送。

## Validation plan

- Inspector/Graph/Planner/Eval focused pytest。
- `npm.cmd run eval:standard` 与 20 条结构化评测顺序执行。
- 前端生产构建、`git diff --check`。

## Risks

- 业务形态改为建议后，可能让安全但口径不正确的 SQL 通过；因此结构化结果评测、warning 和明确业务合同的 Repair 仍必须保留。
- 云端模型波动会影响真实 20 条结果，需分开报告生成失败、执行成功与行匹配。
