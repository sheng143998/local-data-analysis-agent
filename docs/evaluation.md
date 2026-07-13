# 评估说明

## 目标

评估用于回答两个问题：

- 主链路是否可运行。
- SQL 是否更接近期望语义。

## 数据集

标准问题集：

```text
eval/datasets/standard_questions.jsonl
```

快速回归集当前包含 20 个标准问题，覆盖：

- 基础查询。
- 复杂指标。
- 用户分析。
- 漏斗与营销。

每条数据包含：

- `id`
- `category`
- `question`
- `expected_tables`
- `expected_keywords`

## Authenticated 真值评测

真实数据库质量基线使用：

```text
eval/datasets/database_ground_truth_questions.jsonl
```

该数据集包含 50 条来自 `C:\Users\admin\Desktop\新建 文本文档.txt` 的问题和真值答案，覆盖基础实体、时间、支付、商品、退款、评价、用户履约以及空结果/不可计算场景。文本对照报告为 `eval/reports/ground_truth_text_alignment.json`，当前核对结果为 50/50、问题差异 0、答案差异 0。

鉴权开启时必须使用专用管理员评测账号：

```bash
npm run eval:database-baseline -- --start 0 --limit 10 --report eval/reports/database_batch_001.json
```

评测脚本从本机未跟踪的 `backend/.env` 读取 `EVAL_AUTH_EMAIL` 和 `EVAL_AUTH_PASSWORD`，在 case 执行前登录并复用会话；缺少凭据或登录失败会直接阻断，不会把 401/403 统计为模型质量失败。分批运行必须使用不同 `--report`，结束后按 case ID 核对完整覆盖。

可信 50-case 对照报告：

```text
eval/reports/post_upgrade_full_eval.json
```

当前结果为执行成功 `31/50`、严格成功 `13/50`、答案匹配 `14/48`。该报告是升级对照基线，不代表质量已经达标；`latest_eval_report.json` 只代表后续标准集运行，不得替代该 50-case 基线。

## 运行命令

```bash
npm run eval:standard
```

脚本：

```text
eval/scripts/run_eval.py
```

报告：

```text
eval/reports/latest_eval_report.json
```

## 报告字段

- `total`：问题数量。
- `success_count`：链路成功数。
- `strict_success_count`：严格断言成功数。
- `execution_success_rate`：HTTP 200、SQL 非空、Guard 通过。
- `strict_success_rate`：链路成功且命中期望表和关键词。
- `sql_generation_success_rate`：SQL 非空比例。
- `table_match_rate`：期望表命中比例。
- `keyword_match_rate`：期望关键词命中比例。
- `memory_hit_rate`：fast_path 比例。
- `reuse_success_rate`：fast_path 且执行成功比例。
- `average_latency_ms`：平均耗时。
- `path_counts`：路径分布。
- `failures`：链路失败案例。
- `assertion_failures`：链路成功但断言失败案例。
- `assertion_failure_summary`：断言失败聚合诊断，包含缺失表、失败类别、失败路径和 case id 列表。
- `cases[].run_id`：该评估问题对应的 `query_runs.id`，用于开发者追踪。
- `cases[].run_detail_path`：对应开发者调试接口路径，例如 `/api/runs/{run_id}`。
- `cases[].run_trace_summary`：从 `/api/runs/{run_id}` 提取的运行摘要，包含召回表、字段样例、表关系数量、SQL 生成路径、Guard warning/error 和 SQL Memory 规划摘要。
- `assertion_failure_summary.by_missing_table_context_status`：对缺失表做进一步聚合，区分该表是没有进入召回上下文，还是已进入上下文但最终 SQL 没有使用。
- `/api/runs/{run_id}` 的 `analysis_graph.select_generated_sql` 工具调用会包含 `context_table_coverage`，用于判断已召回的非默认业务表是否被最终 SQL 使用。

## 最近标准集工件

标准集最近一次记录：

- 当前本地工件记录为执行 `8/20`、严格 `6/20`；该文件可能随开发运行变化。
- 该标准集工件不替代 authenticated 50-case 基线，也不用于宣称模型质量达标。

这类 20 题报告只用于快速回归；真实质量判断优先使用 authenticated 50-case 对照。

## 如何使用报告

- 如果 `execution_success_rate` 下降，优先检查 API、Guard、Executor、数据库连接。
- 如果 `strict_success_rate` 下降，优先检查 SQL Memory 复用、SQL Generator、schema/metric 召回。
- 如果 `memory_hit_rate` 异常升高且严格成功率下降，说明可能存在错误 fast_path 复用。
- 如果 `assertion_failures` 集中在某类表，优先补强该意图的 schema 召回和 SQL 生成。
- 如果 `assertion_failure_summary.by_missing_table` 集中在某些表，优先检查这些表是否被召回、是否进入模型 SQL prompt、是否被 SQL Memory fast_path 错误绕过。
- 如果某个 case 需要进一步排查，优先打开该 case 的 `run_detail_path`，查看上下文召回、SQL 生成、Guard 和 Executor 的工具调用摘要。
- 如果 `by_missing_table_context_status` 显示 `missing_from_context` 高，优先修 schema/metric 检索；如果显示 `present_in_context` 高，优先修 SQL 生成、SQL Memory 复用或模型路径。
- 如果 `context_table_coverage.missing_tables` 非空，说明表已经进入上下文但当前 SQL 未覆盖；模型开关开启时应优先验证模型 SQL Generator 是否能生成覆盖这些表的查询。
- 流量、优惠券、用户等主题的 schema 召回已加强；如果这些表仍缺失，优先检查字段说明、embedding 同步和业务主题词覆盖。

## 后续方向

- 使用稳定的本地或云端 SQL 模型配置重跑同一 50-case 数据集，比较执行、严格和答案匹配率。
- 按失败分类补齐 Query Plan/Inspector 断言、字段命中、指标口径命中和结果形态断言。
- 评估报告中的 `run_detail_path` 只供开发者排查，普通用户界面不展示评估报告、prompt、模型密钥或原始工具 payload。
