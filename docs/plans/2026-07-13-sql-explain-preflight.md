# SQL EXPLAIN 执行前预检

## Goal

在 SQL Guard 放行后、主查询执行前增加 PostgreSQL `EXPLAIN (FORMAT JSON)` 预检。预检必须采用只读事务和独立超时；任何预检错误、超时或异常均不得执行主查询。

## Scope

- 审阅并扩展 SQL Guard、Executor 和 Analysis Graph 的相邻执行节点。
- 新增结构化 EXPLAIN 预检结果和纯执行工具。
- 将 Guard 放行后的 Graph 路由改为“预检成功才执行主查询”。
- 记录安全摘要，补充 focused tests、模块文档、handoff、提交和推送。

## Out Of Scope

- 不改变 SQL Guard 的允许表、函数、LIMIT 或 SQL 改写规则。
- 不解析或展示业务查询结果，不实现探针查询、成本阈值阻断或自动 Repair。
- 不修改 API、前端、迁移、SQL Prompt 或模型路由。

## Implementation Steps

- [x] 阅读 handoff、项目 skill 和现有 Guard/Executor/Graph 测试边界。
- [x] 定义 EXPLAIN 预检结果与只读、超时、错误处理实现。
- [x] 在 Graph 中接入 Guard 后的条件路由和运行日志。
- [x] 覆盖 Guard 拒绝、预检成功、预检失败/超时和主查询执行顺序。
- [x] 运行 focused tests 和 standard eval；后端全量测试在上一模块的 120 秒上限内未完成，已记录为未通过验证。
- [x] 创建模块记录、更新 handoff、提交并推送。

## Validation Plan

- `backend/tests/test_sql_execution_tools.py` 与 `backend/tests/test_analysis_graph_sql_selection.py` 的 focused pytest。
- `npm.cmd run backend:test`。
- authenticated `npm.cmd run eval:standard`，确认分析链路无意外绕过或安全回退。
- `git diff --check`，以及验证提交只包含本模块文件。

## Risks

- PostgreSQL 的 EXPLAIN 仍会解析、规划并可能访问 catalog；必须在显式只读事务、独立 statement/lock timeout 中运行，且永不拼接不受 Guard 保护的 SQL。
- 预检会增加一次数据库往返和延迟；首版只以成功/失败为门槛，不根据计划成本阻断，避免未校准阈值造成误拒绝。
- 并行模块正在改动 Graph 及运行日志；本模块只修改 Guard 到 Executor 的相邻节点，提交前必须重新核对共享变更。
