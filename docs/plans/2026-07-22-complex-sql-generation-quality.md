# 复杂 SQL 生成质量改进

## Goal

基于 `eval/reports/sql_accuracy_20_memory_current_20260722.json` 的失败样本，修复非 SQL Memory 命中复杂问题的明确业务语义缺口，提高结构化行匹配率；不引入固定 SQL 或削弱 SQL 安全链路。

## Scope

- 修复“成交额”这类明确数据问题被错误澄清的意图识别边界。
- 新增版本化业务合同，覆盖已支付成交额、整体毛利率和品类销售额排行的稳定输出形态。
- 让已有 Query Plan 将这些合同的来源表、来源字段、过滤条件、聚合和别名传递给生成与一次定向 Repair。
- 增加意图解析、语义解析、Planner 和迁移回归测试。

## Out of scope

- 不写入问题到 SQL 的固定映射或执行兜底 SQL。
- 不移除或放宽 Intent 校验、SQL Guard、`EXPLAIN`、只读 Executor 与资源限制。
- 不把外部模型的单次成功视为确定性质量结论。

## Implementation steps

- [x] 为明确成交额问题补齐意图与对话路由的业务对象识别，并添加回归测试。
- [x] 新增语义合同 migration：已支付订单成交额、整体毛利率，以及品类销售额排行的最新输出别名版本。
- [x] 为 Resolver 和 Query Planner 增加合同选择与 Query Plan 断言。
- [x] 应用本地 PostgreSQL migration，运行聚焦测试和标准评测。
- [x] 使用新的报告与 checkpoint 重跑相同 20 条数据集，比较结构化行匹配、执行成功、Memory 命中和延迟。
- [x] 记录完成情况、验证证据、残余失败分类；因与工作区已有未提交改动共享文件，未安全分离出可独立提交的变更。

## Validation plan

- `.venv\\Scripts\\python.exe -m pytest backend/tests/test_question_intent_parser.py backend/tests/test_semantic_resolver.py backend/tests/test_query_planner.py backend/tests/test_db_migrations.py -q`
- `npm.cmd run eval:standard`
- `eval/scripts/run_eval.py --dataset eval/datasets/sql_accuracy_20_sample.jsonl`，使用新的 report/checkpoint。
- `git diff --check`。

## Risks

- 合同只能约束模型输入和 Repair 目标，无法保证每次外部模型输出都遵循；必须以结构化行结果验证。
- “成交额”按本评测数据集定义为已支付订单成交额；该口径通过显式合同声明，不能隐式推广到未知业务域。
- 新合同可能与旧泛化合同同时匹配，必须用版本和 `replaces_contract_keys` 消除冲突。
