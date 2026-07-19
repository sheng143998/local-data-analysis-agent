# 品类商品排行合同修复

## Goal

让“订单商品数量最多的前 N 个商品品类，同时展示订单商品数量和销售额”生成可验证的 SQL：按订单商品明细累计销售额，按订单商品数排行，并避免同义词导致的错误合同拦截。

## Scope

- 归一化 Planner 中的商品品类同义词，保证它们只生成 `category` 一个维度、输出别名和排序要求。
- 新增版本化的品类订单商品数与销售额排行语义合同，并让更具体合同替代泛化销售额合同的来源约束。
- 在 Query Plan/Inspector/Graph 替身模型测试中覆盖正确 SQL、重复订单金额 SQL 被拦截、Top N 和同义词场景。

## Out of scope

- 不添加固定 SQL 模板，不放宽 SQL Guard、EXPLAIN 或只读 Executor。
- 不通过增加模型重试次数掩盖外部模型的超时或结构化输出问题。

## Implementation steps

- [x] 补充语义合同和语义解析的特异性选择规则。
- [x] 修复维度同义词归一化和合同合并后的 Query Plan。
- [x] 增加 focused 测试，验证首次正确候选能通过合同校验。
- [x] 运行 focused pytest、真实数据库只读校验与前端构建。
- [x] 更新模块记录与 handoff，提交并推送本模块。

## Validation plan

- `test_semantic_resolver.py`、`test_query_planner.py`、`test_sql_inspector.py`、`test_analysis_graph_sql_selection.py`。
- 对目标问题构造正确的 PostgreSQL SQL，经 Query Plan、Inspector 和 Guard 验证，并在本地数据库只读执行。
- `npm.cmd run frontend:build`，确认本次后端合同变更不破坏前端契约。

## Risks

- 外部 SQL 模型仍可能超时、空响应或不遵从结构化输出；本模块只保证正确 SQL 的口径与安全链路可通过，不把模型不稳定性伪装为成功。
- 合同选择必须仅替代同一业务口径中的泛化合同，不能丢弃其他用户明确请求的指标。
