# 标准问题评估集基础设施完成说明

模块：标准问题评估集基础设施

当前状态：已完成实现、测试、真实评估运行和文档更新，等待提交并推送到 GitHub。

业务逻辑：

- 开发者运行 `npm run eval:standard`，系统会读取 `eval/datasets/standard_questions.jsonl` 中的 20 个 V1 标准问题。
- 评估脚本逐条调用 `/api/analyze`，记录 HTTP 状态、SQL 是否生成、SQL Guard 是否通过、返回行数、路径类型、记忆命中和耗时。
- 评估报告输出到 `eval/reports/latest_eval_report.json`。
- 当前评估先衡量“链路是否可运行”，不把营销/漏斗问题的语义准确性包装成已完成；语义准确率会在真实模型和更严格断言接入后继续增强。

关键代码：

- `eval/datasets/standard_questions.jsonl`
  - 包含 20 个草案标准问题，覆盖基础查询、复杂指标、用户分析、漏斗与营销。
- `eval/scripts/run_eval.py`
  - `load_cases()`：读取 JSONL 数据集。
  - `run_cases()`：可注入 analyze 函数，默认通过 FastAPI TestClient 调用 `/api/analyze`。
  - `summarize_results()`：统计执行成功率、SQL 生成成功率、记忆命中率、复用成功率、平均延迟、路径占比、失败案例。
  - `write_report()`：写入 JSON 报告。
- `backend/tests/test_eval_runner.py`
  - 覆盖数据集数量、评估执行和指标汇总。
- `package.json`
  - 新增 `npm run eval:standard`。

数据契约：

- Dataset JSONL：
  - `id`
  - `category`
  - `question`
  - `expected_tables`
  - `expected_keywords`
- Report JSON：
  - `total`
  - `success_count`
  - `execution_success_rate`
  - `sql_generation_success_rate`
  - `memory_hit_rate`
  - `reuse_success_rate`
  - `average_latency_ms`
  - `path_counts`
  - `failures`
  - `cases`

验证：

- `npm run backend:test`：70 passed，1 个 `StarletteDeprecationWarning`。
- `npm run eval:standard`：20/20 链路执行成功，`execution_success_rate=100.00%`，生成 `eval/reports/latest_eval_report.json`。

风险/后续：

- 当前评估成功代表 API 链路、SQL Guard 和执行闭环成功，不代表每个问题语义已经完全正确。
- 部分用户分析、漏斗和营销问题仍会走确定性回退路径。
- 后续需要在 `MODEL_SQL_GENERATOR_ENABLED=true` 和真实模型服务下运行评估，并增加更严格的表命中、字段命中、指标口径和结果形态断言。
