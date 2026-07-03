# 标准问题评估说明

## 目标

评估用于回答两个问题：

- 主链路是否可运行。
- SQL 是否更接近期望语义。

## 数据集

标准问题集：

```text
eval/datasets/standard_questions.jsonl
```

当前包含 20 个 V1 标准问题，覆盖：

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

## 最近基线

最近一次评估：

- 20/20 链路执行成功。
- `execution_success_rate=100%`。
- `strict_success_rate=55%`。
- SQL Memory 关键表约束后，`memory_hit_rate` 从 100% 降为 60%。

这说明主链路稳定，但语义覆盖仍需提升。

## 如何使用报告

- 如果 `execution_success_rate` 下降，优先检查 API、Guard、Executor、数据库连接。
- 如果 `strict_success_rate` 下降，优先检查 SQL Memory 复用、SQL Generator、schema/metric 召回。
- 如果 `memory_hit_rate` 异常升高且严格成功率下降，说明可能存在错误 fast_path 复用。
- 如果 `assertion_failures` 集中在某类表，优先补强该意图的 schema 召回和 SQL 生成。

## 后续方向

- 在真实本地模型可用后，开启 `MODEL_SQL_GENERATOR_ENABLED=true` 跑评估。
- 增加字段命中、指标口径命中和结果形态断言。
- 将失败案例关联到 `query_runs` 和 `tool_calls`。
