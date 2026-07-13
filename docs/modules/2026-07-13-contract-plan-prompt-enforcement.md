# Contract And Plan Prompt Enforcement Experiment

## Result

- 增加 snapshot contract 优先 Prompt 后，focused `48 passed`。
- authenticated 前 10 条从 `7/10` 执行、`3/10` 严格、`3/10` 答案匹配，下降至 `6/10`、`2/10`、`2/10`。
- 因真实 benchmark 回归，Prompt 强约束已撤回；报告保留于 `eval/reports/contract_plan_prompt_batch_001.json`。

## Decision

- 不以单次 Prompt 规则替代 Query Plan/Inspector。
- 后续针对失败类别使用受审核契约/verified SQL 或模型对比，并以同一数据集验证。
