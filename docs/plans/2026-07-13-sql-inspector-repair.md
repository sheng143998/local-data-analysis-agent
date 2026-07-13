# SQL Inspector And Categorized Repair

## Goal

在 Guard 前独立检查 SQL 与 Query Plan 的实体、度量、维度、时间、排序和输出形态对齐，并将失败分类传给已有 repair 链路。

## Scope

- 新增 AST 驱动 Inspector 与结构化 issue 分类。
- 在生成后验证节点合并 Inspector 结果，最多保持现有两次 repair 上限。
- 记录 inspector 结果用于 run trace。

## Out of scope

- 不替代 SQL Guard、Executor 或完整 EXPLAIN/探针查询。

## Implementation steps

- [x] 实现 Plan 对齐检查与分类 issue。
- [x] 接入 Graph repair context 和测试。
- [x] 全量验证、文档、commit、push。

## Validation plan

- Inspector/Graph focused pytest、后端全量和 authenticated eval 抽样。

## Risks

- AST 对别名和复杂 CTE 只能保守检查，无法证明所有业务口径；无法判断时不得放宽 Guard。
