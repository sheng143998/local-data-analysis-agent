# SQL 生成速度二十样本基准优化

## Goal

建立至少 20 条带结构化参考结果的 SQL accuracy 样本，并在该样本上逐项优化 SQL 生成速度；准确率下降或速度无显著改善的修改自动回退。

## Scope

- 新增 20 条跨订单、支付、商品、退款、用户、履约和评价的结构化准确率样本。
- 记录基准和每项试验的 strict/row match、SQL 生成 p50/p95、端到端平均耗时和超时率。
- 首次单独评估 SQL 输出 token 上限，不与 Context Pack 改动叠加。

## Out of scope

- 不修改 Inspector、Guard、EXPLAIN、Executor 或业务合同来制造速度收益。
- 不以低于 20 条的样本宣称优化有效。

## Implementation steps

- [x] 生成并验证 20 条结构化参考结果样本。
- [x] 使用逐条 checkpoint 完成当前基准。
- [x] 单独降低 SQL 输出 token 上限并复测；准确率持平但 SQL 生成/端到端平均延迟恶化，已回退。
- [ ] 完成回归、报告、提交与推送。

## Validation plan

- 至少 20 条样本严格和行结果匹配。
- 与基准相比，准确率不下降且 SQL 生成 p50/p95 或平均耗时有明确改善。
- focused pytest、前端构建与差异检查。

## Risks

- 云端模型延迟波动较大，需报告每条与分位数，不能只比较一次均值。
