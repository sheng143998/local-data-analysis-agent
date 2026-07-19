# SQL 生成速度基准优化

## Goal

从多个角度优化 SQL 生成速度，以结构化准确率 smoke 和节点耗时为门槛；准确率下降或速度无收益的改动必须回退。

## Scope

- 对 Prompt Context Pack 与模型输出契约分别进行受控优化。
- 使用三条多表结构化准确率 smoke 比较严格成功率、行匹配率、SQL 生成平均耗时和 API 平均耗时。
- 记录保留与回退决策，不改变 Inspector、Guard、EXPLAIN 或只读执行边界。

## Out of scope

- 不靠降低安全校验、增加固定 SQL 或放宽模型错误处理换取速度。
- 不把单次随机延迟变化当作可保留优化。

## Implementation steps

- [x] 记录基准并试验合同优先 Context Pack 裁剪。
- [x] 对无速度收益的 Context Pack 裁剪执行回退。
- [x] 试验最小 SQL JSON 输出契约并复测准确率与耗时。
- [x] 运行最终回归、更新记录、提交与推送。

## Validation plan

- 多表 smoke 的结构化行匹配必须保持 `3/3`。
- SQL 生成与端到端平均耗时必须低于基准，否则回退。
- Model Generator/Graph/Eval focused tests、前端构建与差异检查。

## Risks

- 云端模型延迟存在波动；基准结论应继续用更大的参考结果集复测。
