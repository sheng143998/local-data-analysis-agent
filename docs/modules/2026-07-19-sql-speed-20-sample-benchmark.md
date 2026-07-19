# SQL 生成速度二十样本基准优化

## Completed behavior

- 新增 `eval/datasets/sql_accuracy_20_sample.jsonl`，包含 20 条订单支付、品类排行、成本毛利、退款、城市和复购问题；每条均有结构化 `expected_rows`。
- `eval/scripts/run_eval.py` 现在在每条案例结束后原子写入 checkpoint，默认路径为报告同名的 `.checkpoint.json`；`--resume` 只执行缺失案例，并拒绝不同案例列表或损坏 checkpoint。
- 最终报告也采用原子写入，外部中断不会再把半份 JSON 当作有效报告。

## Key decisions

- 保持严格顺序执行，不引入并行评测或放宽 Inspector、Guard、EXPLAIN、只读 Executor。
- 以结构化行匹配、严格成功率、SQL 生成 p50/p95、端到端 p50/p95 和 HTTP 状态共同判断优化结果。
- 只评估单一变量：将 SQL 模型最大输出 token 从 `1200` 改为 `700`。20 条实验中准确率未改善，且平均与 p95 延迟恶化，故已回退到 `1200`。

## API/data-contract impact

- 无外部 API 改动。
- Eval CLI 新增 `--checkpoint` 和 `--resume`；checkpoint 仅为本地可恢复评测状态，不应提交。

## Evaluation evidence

| 指标 | 基准（1200） | 实验（700） | 结论 |
| --- | ---: | ---: | --- |
| 执行成功率 | 60% | 60% | 持平 |
| 严格成功率 | 35% | 35% | 持平 |
| 结构化行匹配率 | 40% | 40% | 持平 |
| SQL 生成平均 | 22.89s | 27.01s | 恶化，回退 |
| SQL 生成 p50 | 17.35s | 19.69s | 恶化，回退 |
| API 平均 | 57.32s | 67.48s | 恶化，回退 |
| API p95 | 128.84s | 176.83s | 恶化，回退 |

- 基准：`eval/reports/sql_accuracy_20_checkpointed_baseline_20260719.json`，完整 `20/20`。
- 实验：`eval/reports/sql_accuracy_20_max_tokens_700_20260719.json`，完整 `20/20`。
- 上述报告与 checkpoint/日志都是本地评测工件，不纳入提交。

## Validation

- `.venv\\Scripts\\python.exe -m pytest backend/tests/test_model_sql_generator.py backend/tests/test_eval_runner.py backend/tests/test_analysis_graph_sql_selection.py`
- `npm.cmd run frontend:build`
- `git diff --check`

## Remaining risks and follow-up

- 20 条中有 7 条 HTTP 503，模型服务的可用性与 Repair 长尾仍是主要性能问题；数据库执行平均约 0.26s，不是当前瓶颈。
- 下一轮应针对模型请求排队、首响应或 Repair 调用做单变量、可观察的优化，并继续使用相同 20 条样本和回退门槛。
