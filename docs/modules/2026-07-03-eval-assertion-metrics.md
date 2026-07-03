# 标准问题评估断言增强完成说明

模块：标准问题评估断言增强

当前状态：已完成实现、测试、真实评估运行和文档更新，等待提交并推送到 GitHub。

业务逻辑：

- 原评估只能说明 `/api/analyze` 链路是否成功返回 SQL、通过 Guard 并得到结果。
- 本模块把评估拆成两层：
  - `ok`：链路成功，代表 HTTP 200、SQL 非空、SQL Guard 通过。
  - `strict_ok`：链路成功且命中标准问题定义的期望表和关键词。
- 评估命令不会因断言失败直接失败，而是把断言失败写入报告，帮助开发者定位能力缺口。

关键代码：

- `eval/scripts/run_eval.py`
  - `EvalCaseResult` 新增 `missing_tables`、`missing_keywords`、`table_match`、`keyword_match`、`strict_ok`。
  - `summarize_results()` 新增 `strict_success_count`、`strict_success_rate`、`table_match_rate`、`keyword_match_rate`、`assertion_failures`。
  - CLI 输出新增 `strict_success_rate`。
- `backend/tests/test_eval_runner.py`
  - 覆盖链路成功和断言成功分离的场景。
  - 覆盖 SQL 执行成功但未命中期望表/关键词时进入 `assertion_failures`。
- `eval/reports/latest_eval_report.json`
  - 已更新为增强后的报告结构。

数据契约：

- `EvalCaseResult`：
  - `ok`
  - `strict_ok`
  - `table_match`
  - `keyword_match`
  - `missing_tables`
  - `missing_keywords`
- Report：
  - `execution_success_rate`
  - `strict_success_rate`
  - `table_match_rate`
  - `keyword_match_rate`
  - `assertion_failures`

验证：

- `npm run backend:test`：71 passed，1 个 `StarletteDeprecationWarning`。
- `npm run eval:standard`：20/20 链路执行成功，`strict_success_rate=55.00%`。
- 断言失败共 9 个，主要集中在用户、流量和优惠券问题，暴露出 SQL Memory 快速复用对表/意图约束不足。

风险/后续：

- 表/关键词断言仍是启发式，不等于最终业务语义正确性。
- 下一步应增强 SQL Memory Reuse Planner，让 fast_path 复用必须满足更严格的表/指标/意图约束。
- 后续可继续增加字段命中、指标口径命中和结果形态断言。
