# 模块：评估报告 Run Trace 关联

当前状态：本模块已完成代码开发、文档更新、完整验证、commit 和 push。提交信息为 `新增评估RunTrace关联并通过验证`，已推送到 GitHub。该模块只增强开发者评估报告，不改变普通用户前端，不新增固定 SQL 模板，也不改变 `/api/analyze` 业务响应契约。

业务逻辑：开发者运行 `npm run eval:standard` 后，报告中的每个 case 都会携带 `run_id` 和 `run_detail_path`。当某个问题严格断言失败时，可直接打开 `/api/runs/{run_id}` 查看该问题的上下文召回、SQL 生成 warning、Guard 摘要和执行状态，减少从评估失败到运行诊断之间的手工查找成本。

关键代码：

- `eval/scripts/run_eval.py`
  - `EvalCaseResult` 新增 `run_id` 和 `run_detail_path`。
  - `analyze_with_test_client()` 在调用 `/api/analyze` 后读取 `/api/runs?limit=5`，匹配当前问题最近运行记录，并把 `_eval_run_id` / `_eval_run_detail_path` 注入评估内部 body。
  - `run_cases()` 通过 `_extract_eval_run_trace()` 把 trace 字段落到最终 case result。
  - `_find_latest_run_id()` 读取开发者 runs 接口，失败时返回 `None`，不影响评估主链路。
- `backend/tests/test_eval_runner.py`
  - 覆盖 report 保留 run trace、trace 字段提取和最近 run 匹配逻辑。

数据契约：

- `eval/reports/latest_eval_report.json` 的 `cases[]`、`failures[]` 和 `assertion_failures[]` 中新增：
  - `run_id`: string 或 null。
  - `run_detail_path`: string，例如 `/api/runs/{run_id}`。
- FastAPI 业务接口响应不变。
- 数据库结构不变。

验证：

- `py -3 -m pytest backend/tests/test_eval_runner.py`，6 passed，1 个 `StarletteDeprecationWarning`。
- `npm run backend:test`，147 passed，1 个 `StarletteDeprecationWarning`。
- `npm run eval:standard`，20/20 链路成功，严格成功率 55%。
- 抽查 `eval/reports/latest_eval_report.json`：20 个 case 均包含 `run_id` 和 `run_detail_path`，9 个断言失败项均包含 `run_id`。
- `npm run frontend:build` 已通过。
- `npm run test:e2e` 已通过，1 个 `StarletteDeprecationWarning`。

风险/后续：

- 当前通过“最近 5 条 runs 中匹配相同问题”建立关联；标准评估是串行执行，因此可用。未来如果评估改成并发，应增加请求级 correlation id。
- `/api/runs` 仍是开发者调试接口，上线或多人使用前需要权限控制。
