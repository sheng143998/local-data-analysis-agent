# 批量评测耗时与日志可观测性

## Completed behavior

- `run_eval.py` 的报告新增 `performance_summary`：按 API 总耗时、Graph 已知节点耗时、未归因耗时和每个 Graph 节点输出 count、total、avg、p50、p95、max。
- 单 case 保留现有 `run_trace_summary`，并补充 SQL 模型路由摘要和 Repair 次数；已有的 Guard、EXPLAIN、Executor、检索表和最慢节点继续保留。
- `run_targeted_contract_eval.py` 每完成一条 case 就原子写入 checkpoint，并输出 case ID、HTTP 状态、API 耗时和最慢节点。
- `--resume` 会读取同一报告中已完成的 case 并跳过它们；中途超时后可从剩余 case 继续，避免重复消耗云端模型调用。

## Interpretation

- `api_total` 是端到端评测请求耗时。
- `graph_known` 是已记录 Graph 节点之和。
- `unattributed` 是 API 总耗时减去 Graph 已知节点，可能包含 Router、意图模型、鉴权、会话持久化、网络与日志写入；不会伪装为某个具体模块。

## Validation

- `python -m pytest backend/tests/test_eval_runner.py -q`：`18 passed, 1 warning`。
- `python -m compileall -q eval/scripts`：通过。
- `git diff --check`：通过。

## Remaining risks

- 当前 Graph 的节点耗时不包含 Router 与 AgentService 内的每个子步骤，因此它们体现为未归因耗时。下一步可为 Router 和 Intent 增加同样的安全摘要计时。
- checkpoint 仅保护已完成 case；单条模型调用被外部超时中断时仍需重试该条。

## Delivery

- 代码、测试、计划、handoff 和模块记录会提交推送；`eval/reports` 继续保持本地工件。
