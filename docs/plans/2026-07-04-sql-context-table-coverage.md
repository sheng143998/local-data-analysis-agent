# 计划：SQL 关键上下文表覆盖检查

## Goal
解决“表已经被 schema/metric 检索召回，但 SQL Memory rewrite 或确定性生成仍没有使用这些关键表”的问题，减少旧 SQL 记忆覆盖新业务问题的情况。

## Current task
当前正在做：在 SQL 选择阶段增加通用上下文表覆盖检查和诊断，不新增固定 SQL 模板。

## Scope
包含：
- 从 `RetrievalContext.tables` 和生成 SQL 中计算上下文表覆盖情况。
- 对非默认业务表缺失的 SQL 增加 warning。
- 当模型 SQL Generator 显式开启且当前 SQL 缺少关键上下文表时，尝试改走模型 cold path。
- 将覆盖诊断写入 run trace，便于 eval 报告继续定位。
- 增加 focused tests，更新 handoff 和模块完成文档。

不包含：
- 不新增用户问题到固定 SQL 的模板。
- 不修改普通用户 UI，不展示调试诊断。
- 不强制依赖真实模型或真实 API key。

## Module boundary
上游输入：`RetrievalContext`、`SqlReusePlan`、用户问题、模型开关。
下游输出：`GeneratedSql`、run trace tool call payload、评估诊断可读字段。
可能触达文件：
- `backend/app/agents/analysis_graph.py`
- `backend/tests/test_analysis_graph_sql_selection.py`
- `docs/modules/2026-07-04-sql-context-table-coverage.md`
- `docs/handoff/current.md`
- `README.md` 或相关 docs

## Business logic
当用户问新增用户、流量来源、优惠券核销等问题时，检索层已经召回 `users`、`traffic_events`、`coupons`、`coupon_usages` 等表。如果最终 SQL 只查询订单销售表，系统应识别为上下文覆盖不足：
- 对开发者运行记录输出缺失表诊断。
- 如果模型生成开关开启，优先让模型根据已召回 schema 重新生成 SQL。
- 如果模型关闭，仍返回当前可执行结果，但带内部 warning，后续评估可识别问题来源。

## Data contract
`GeneratedSql.warnings` 增加内部诊断文本，不进入普通用户主界面。
`analysis_graph.select_generated_sql` 工具调用 output 增加：
- `context_table_coverage.required_tables`
- `context_table_coverage.sql_tables`
- `context_table_coverage.missing_tables`
- `context_table_coverage.covered`

## Implementation steps
任务清单：
- [x] 阅读 handoff、skill、相关源代码和测试。
- [x] 增加 SQL 表抽取和上下文覆盖检查。
- [x] 接入 SQL 选择路径和 run trace 输出。
- [x] 增加 focused tests。
- [x] 运行 focused tests、后端测试、评估、前端构建和 e2e。
- [x] 更新模块文档、handoff。
- [x] commit 并 push。

## Validation plan
- `py -3 -m pytest backend/tests/test_analysis_graph_sql_selection.py`
- `npm run backend:test`
- `npm run eval:standard`
- `npm run frontend:build`
- `npm run test:e2e`

## Risks and open questions
- 模型默认关闭时，系统仍只能记录诊断并回退确定性 SQL，严格成功率未必立即提升。
- 关键上下文表规则需要避免误伤正常的订单/支付/商品基础查询，因此先只把非默认扩展业务表作为强覆盖要求。
