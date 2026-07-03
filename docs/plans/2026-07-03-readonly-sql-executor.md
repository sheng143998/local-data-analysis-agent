# 只读 SQL Executor 计划

Goal: 实现只读 SQL Executor，确保数据库执行只接受 SQL Guard 放行后的 `final_sql`。

当前正在做：模块已完成，只读 SQL Executor 已实现并通过验证。

Scope:
- 包含：Pydantic 执行结果 schema、Executor 工具、真实 PostgreSQL 执行测试、模块文档、handoff 更新。
- 不包含：接入 `/api/analyze`、查询运行日志写入、SQL Repair。

Module boundary:
- Upstream inputs: `SqlGuardResult.final_sql`
- Downstream outputs: `SqlExecutionResult`
- Likely touched files: `backend/app/schemas`, `backend/app/tools`, `backend/tests`, `docs/`。

Business logic:
- LLM 生成 SQL 不能直接执行。
- Executor 只接受 Guard 返回的 allowed result。
- 执行结果包含列、行、行数、耗时、状态和错误信息。

Data contract:
- `SqlExecutionResult`: `status`, `columns`, `rows`, `row_count`, `latency_ms`, `error_message`

Implementation steps:
- [x] 创建计划
- [x] 添加执行结果 schema
- [x] 实现只读 SQL Executor
- [x] 添加真实数据库执行测试
- [x] 运行验证
- [x] 更新 handoff 和模块文档
- [x] commit 并 push

Validation plan:
- `npm run backend:test`
- `npm run test:e2e`
- `npm run frontend:build`

Risks and open questions:
- 当前测试打本地 `local_data_agent`，后续应拆独立测试库。
- 当前 Executor 只做同步执行，后续可增加超时、取消和 query_runs 记录。
