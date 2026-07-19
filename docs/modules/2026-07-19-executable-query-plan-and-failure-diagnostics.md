# 模块：可执行 Query Plan 与失败诊断修复

## 已完成行为

- Query Plan 新增 `execution_contract`，可表达绑定后的时间字段和半开时间谓词、时间分组表达式、规范过滤、关联/去重策略、聚合粒度与稳定技术别名。
- 已支付订单的销售额、订单数月度查询会明确绑定 `orders.purchase_at`、`payments.status = 'paid'`、订单粒度以及 `month`、`sales_amount`、`order_count` 输出别名。自然语言过滤“已支付订单”会被替换为规范谓词，避免 Inspector 将同一规则误判为两条过滤。
- SQL 生成和 Repair Payload 将 `execution_contract` 作为不可变更的本次业务合同，并将其转换为可复制的修复规则。
- `GET /api/runs/{run_id}` 的管理员详情在 `debug_summary.sql_generation.sql_candidates` 中返回首次生成与 Repair 的最小 SQL 候选摘要；不记录模型推理、完整 Prompt、密钥或原始模型文本。运行列表和普通聊天响应不返回该字段。
- 前端对 503 显示“模型未生成符合已确认业务口径的安全查询，系统未执行数据库”，不再要求用户在信息已充分时换一个更具体的问题。

## 关键决策

- 执行合同只在已确认指标、时间和支付口径的范围内补齐，不生成固定业务 SQL，也不放宽 Inspector、Guard、EXPLAIN 或只读 Executor。
- 支付订单金额使用订单粒度约束，允许模型使用 `EXISTS` 或先去重支付订单后关联，禁止在多条 payments 行上直接累计 `orders.total_amount`。
- 候选 SQL 是管理员诊断信息，复用现有受管理员角色保护的运行详情和工具调用 JSON，不新增普通用户 API 或数据库迁移。

## API 与数据影响

- `GET /api/runs/{run_id}` 的 `debug_summary.sql_generation` 新增 `sql_candidates`，每项包含 `stage`、`path`、`sql`、`warning_count`。
- `query_runs` 和 `tool_calls` 表结构未改变；候选 SQL 写入既有 `tool_calls.output_payload`。
- `POST /api/analyze` 在未生成安全 SQL 时仍返回 503，但详情文案改为真实的业务口径失败原因。

## 验证

- `python -m compileall backend/app` 通过。
- `python -m pytest backend/tests/test_query_planner.py backend/tests/test_model_sql_generator.py backend/tests/test_sql_inspector.py backend/tests/test_analysis_graph_sql_selection.py backend/tests/test_run_service.py -q`：`65 passed`。
- `npm.cmd run frontend:build` 通过；仅有既有 bundle 大小提示。
- 真实认证请求“2017 年每个月已支付订单的销售额和订单数分别是多少？按月份升序展示。”：运行 `3fb6119c-efe4-444b-8727-9d5f904f1dd7`，Guard `allowed`、执行 `success`、返回 12 行、总耗时 30956ms。最终 SQL 使用 `orders.purchase_at`、已支付 `EXISTS` 条件、订单去重计数与按月升序；管理员详情可见生成候选 SQL。
- 一次旧的 `backend/tests/test_runs.py` 集成尝试因云端模型在“最近 30 天销售额按天变化”场景未生成符合旧断言的 SQL 返回 503，不能视为全量后端测试通过；本模块目标问题已通过真实回归。

## 剩余风险与后续

- 云端模型仍可能在未覆盖的复杂合同中不遵从执行合同；必须继续按 run trace 分类并以真实评测验证，不可退回固定 SQL。
- 管理员候选 SQL 诊断目前通过后端接口查看；需要独立开发者界面时应另行设计分页、审计与脱敏策略。
