# SQL EXPLAIN 执行前预检

## Completed behavior

- `explain_guarded_sql()` 只接收已放行的 Guard 结果，在独立只读事务中运行 `EXPLAIN (FORMAT JSON)`，并使用独立、更短的 statement timeout 和 lock timeout。
- Analysis Graph 现在固定为 `Guard -> EXPLAIN -> Executor`。预检失败或超时会构造错误执行状态，进入一次有限修复；再次失败则结束，绝不执行主查询。
- Run Trace 新增 `sql_execution_tools.explain_guarded_sql` 的安全摘要和 `sql_explain` 节点耗时，不持久化完整执行计划。

## Key decisions

- 本期仅校验预检可成功，不根据成本或扫描行数阻断，避免未校准阈值造成业务误拒绝。
- EXPLAIN 不绕过任何边界：SQL 仍先经过 QuerySpec/Inspector/Guard，主查询仍由只读 Executor 执行。

## API and data-contract impact

- 无公开 API、前端或数据库 migration 变更。
- 内部增加 `SqlExplainResult` 及运行 trace 工具调用。

## Validation

- `.venv\\Scripts\\python -m pytest backend/tests/test_sql_execution_tools.py backend/tests/test_analysis_graph_sql_selection.py backend/tests/test_runs.py`：`44 passed, 1 warning`。
- `npm.cmd run backend:test`：本轮未重新运行；上一模块运行在 120 秒上限内未完成，不能视为通过。
- `npm.cmd run eval:standard`：`8/20` 执行成功、`6/20` 严格成功。失败 trace 的 `sql_explain` 均为 `0ms`，说明失败发生在模型生成/意图验证前置路径，没有证据显示 EXPLAIN 造成执行回归或绕过。

## Remaining risks and follow-up

- 预检增加一次数据库往返；需要在完整 50-case 模型稳定性对照中测量延迟影响。
- 当前标准集质量低于历史快照，根因是模型无 SQL/错误 SQL；应与语义契约和模型 benchmark 分开治理，不能通过绕过预检恢复成功率。
