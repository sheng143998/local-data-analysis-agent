# Query Plan And Context Pack

## Goal

在 SQL 生成前构造结构化 Query Plan，并依据计划裁剪 Context Pack，使模型不得自由改变已解析的指标、维度、时间和输出形态。

## Scope

- 定义 Query Plan schema 和确定性 planner。
- 从 QuerySpec、resolved contracts 和 intent 构造实体、measures、dimensions、filters、排序、limit 和 expected shape。
- 将 Query Plan 传入 retrieval context 与 SQL generator payload。
- 补充 plan 构造和 payload 测试。

## Out of scope

- 不让 Plan 直接执行 SQL，不移除现有 Validator/Guard/Executor。
- 不实现 Inspector、EXPLAIN、Result Contract 或模型路由。

## Implementation steps

- [x] 新增 Query Plan 数据契约和 planner。
- [x] 贯通 Graph、Context Builder 与 SQL generator payload。
- [x] 聚焦/全量测试、文档、commit、push。
- [ ] authenticated 评测抽样与 Inspector 模块统一对照。

## Validation plan

- planner/model SQL payload/Graph focused pytest，后端全量和 authenticated eval 抽样。

## Risks

- 已有 QuerySpec 不完整时 Plan 必须保持开放的未知字段，而不是猜测业务口径。
