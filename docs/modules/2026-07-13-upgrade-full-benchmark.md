# Upgrade Full Benchmark

## Result

| Metric | Before Upgrade | After Upgrade |
| --- | ---: | ---: |
| Execution success | 28/50 (56.00%) | 31/50 (62.00%) |
| Strict success | 11/50 (22.00%) | 13/50 (26.00%) |
| Answer match | 10/48 (20.83%) | 14/48 (29.17%) |

## Evidence

- Baseline: `eval/reports/latest_eval_report.json`.
- Upgrade result: `eval/reports/post_upgrade_full_eval.json`.
- Both runs use the authenticated evaluation account and the same 50-case database ground truth set.

## Interpretation

- 当前升级提高了执行稳定性、SQL 结构断言和真值匹配，但仍远低于草案的生产质量门槛。
- 下一步不应继续增加固定 SQL；应根据 failures 的实体/聚合类别扩展审核语义契约、审核 verified SQL，并比较 SQL 模型。
