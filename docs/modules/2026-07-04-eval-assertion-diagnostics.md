# 模块：评估断言失败聚合诊断

当前状态：本模块已完成 eval runner、focused tests、完整验证、commit 和 push。提交信息为 `新增评估断言失败聚合诊断并通过验证`，已推送到 GitHub。它不新增固定 SQL 模板，不改变 `/api/analyze` 主链路，不改变普通用户前端。

业务逻辑：标准评估出现“链路成功但严格断言失败”时，报告会聚合缺失表、失败类别、失败路径和 case id。开发者不用逐条阅读失败列表，就能看到当前语义缺口主要集中在哪里，例如 `users`、`traffic_events`、`coupons` 等表。

关键代码：

- `eval/scripts/run_eval.py`：新增 `assertion_failure_summary` 输出。
- `_assertion_failure_summary()`：按缺失表、类别、路径聚合断言失败。
- `_sorted_count_items()`：按次数降序、名称升序输出稳定结果。
- `backend/tests/test_eval_runner.py`：覆盖报告字段、缺失表聚合、类别聚合、路径聚合和 case id 列表。

数据契约：

- `latest_eval_report.json` 新增 `assertion_failure_summary`。
- 字段包含 `total`、`by_missing_table`、`by_category`、`by_path`、`case_ids`。

验证：

- `py -3 -m pytest backend/tests/test_eval_runner.py`，4 passed，1 个 `StarletteDeprecationWarning`。
- `npm run backend:test`，134 passed，1 个 `StarletteDeprecationWarning`。
- `npm run eval:standard`，20/20 链路成功，严格成功率 55%，报告已生成 `assertion_failure_summary`。
- `npm run frontend:build` 已通过。
- `npm run test:e2e` 已通过，1 个 `StarletteDeprecationWarning`。

风险/后续：

- 本模块只增强诊断，不直接提升严格成功率。
- 后续可把失败 case 关联到 `query_runs` 和 `tool_calls`。
